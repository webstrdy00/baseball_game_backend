from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt, ExpiredSignatureError
from ..auth.utils import SECRET_KEY, ALGORITHM, create_access_token
from ..database import get_db, SessionLocal
from .. import models
import re
from datetime import datetime, UTC
import os

# 인증이 필요하지 않은 경로 패턴
PUBLIC_PATHS = [
    r"^/auth/signup$",
    r"^/auth/token$",
    r"^/auth/login$",
    r"^/auth/logout$",  
    r"^/auth/refresh$",
    r"^/docs",
    r"^/redoc",
    r"^/openapi.json$",
]

# 선택적 인증 경로 패턴 (로그인 없이도 접근 가능하지만, 로그인 정보가 있으면 활용)
OPTIONAL_AUTH_PATHS = [
    r"^/games$",
    r"^/games/\d+$",
    r"^/games/\d+/guesses$",
]

async def auth_middleware(request: Request, call_next):
    """
    모든 HTTP 요청에 대해 인증을 처리하는 미들웨어
    
    1. 공개 경로는 인증 없이 통과
    2. 선택적 인증 경로는 토큰이 없어도 통과하지만, 있으면 사용자 정보 설정
    3. 그 외 경로는 유효한 토큰이 필요
    4. 액세스 토큰이 만료된 경우 리프레시 토큰으로 자동 갱신
    """
    # OPTIONS 요청은 항상 통과시킴 (CORS preflight 요청)
    if request.method == "OPTIONS":
        response = await call_next(request)
        
        # CORS 헤더 추가 - 동적으로 Origin 설정
        origin = request.headers.get("Origin", "*")
        allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        
        if origin in allowed_origins or "*" in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        else:
            response.headers["Access-Control-Allow-Origin"] = allowed_origins[0] if allowed_origins else "*"
        
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
        response.headers["Access-Control-Max-Age"] = "3600"
        
        return response
    
    
    # 요청 경로 확인
    path = request.url.path
    
    # 공개 경로는 인증 없이 통과
    if any(re.match(pattern, path) for pattern in PUBLIC_PATHS):
        return await call_next(request)
    
    # 선택적 인증 경로 확인
    optional_auth = any(re.match(pattern, path) for pattern in OPTIONAL_AUTH_PATHS)
    
    # 토큰 추출 (헤더 또는 쿠키에서)
    access_token = None
    refresh_token = None
    
    # 1. 헤더에서 토큰 추출
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        access_token = authorization.replace("Bearer ", "")
    
    # 2. 쿠키에서 토큰 추출 (헤더에 없는 경우)
    if not access_token:
        access_token = request.cookies.get("access_token")
    
    # 리프레시 토큰 추출 (쿠키에서만)
    refresh_token = request.cookies.get("refresh_token")
    
    # 토큰이 없는 경우
    if not access_token:
        if optional_auth:
            # 선택적 인증 경로는 토큰 없이 통과
            return await call_next(request)
        # 필수 인증 경로는 토큰 없으면 401 에러
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "인증 정보가 없습니다"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 액세스 토큰 검증
    try:
        # 토큰 디코딩 및 검증
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")  # username 대신 email
        user_id = payload.get("id")
        
        # 토큰에 필요한 정보가 없는 경우
        if not email or not user_id:
            if optional_auth:
                return await call_next(request)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "유효하지 않은 토큰입니다"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 요청 상태에 사용자 정보 추가
        request.state.user = {"email": email, "id": user_id}  # username 대신 email
        
    except ExpiredSignatureError:
        # 액세스 토큰이 만료된 경우, 리프레시 토큰으로 갱신 시도
        if refresh_token:
            try:
                # 리프레시 토큰 검증
                refresh_payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
                refresh_email = refresh_payload.get("sub")
                refresh_user_id = refresh_payload.get("id")
                
                if refresh_email and refresh_user_id:
                    # 데이터베이스에서 사용자 확인
                    db = SessionLocal()
                    try:
                        user = db.query(models.User).filter(models.User.id == refresh_user_id).first()
                        if user and user.email == refresh_email:
                            # 새 액세스 토큰 생성
                            new_access_token = create_access_token(
                                data={"sub": user.email, "id": user.id}
                            )
                            
                            # 응답 객체에 새 토큰 설정 (헤더에만)
                            response = await call_next(request)
                            response.headers["Authorization"] = f"Bearer {new_access_token}"
                            
                            # 요청 상태에 사용자 정보 추가
                            request.state.user = {"email": user.email, "id": user.id}
                            
                            return response
                    finally:
                        db.close()
            except:
                pass
            
        # 리프레시 토큰이 없거나 유효하지 않은 경우
        if optional_auth:
            return await call_next(request)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "인증 토큰이 만료되었습니다. 다시 로그인해주세요."},
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    except (JWTError, ValueError):
        # 토큰 파싱 또는 검증 실패
        if optional_auth:
            return await call_next(request)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "유효하지 않은 토큰입니다"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 다음 미들웨어 또는 엔드포인트 호출
    return await call_next(request) 