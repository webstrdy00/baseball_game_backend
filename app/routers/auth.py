from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie, Query
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from .. import models, crud, schemas
from ..database import get_db
from ..auth.utils import SECRET_KEY, ALGORITHM, get_current_user, create_access_token, create_refresh_token
from datetime import datetime, timedelta, UTC
from typing import Optional
import os
from ..auth.utils import verify_token
from ..auth.oauth import process_kakao_login
from fastapi.responses import RedirectResponse
import urllib.parse
import base64
import json
import logging

# 카카오 OAuth 설정
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID", "")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "")

router = APIRouter(
    tags=["인증"],
    responses={404: {"description": "Not found"}},
)

# OAuth2PasswordBearer 설정 수정
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    auto_error=False  # 인증 실패 시 자동 오류 발생 방지
)

"""
새 사용자 등록 엔드포인트
"""
@router.post("/signup", response_model=schemas.UserResponse)
def signup_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.user.create_user(db=db, user=user)

"""
사용자 로그인 엔드포인트 
- JSON 요청으로 로그인
- 액세스 토큰은 헤더에 설정
- 리프레시 토큰은 쿠키에 설정
"""
@router.post("/login", response_model=schemas.LoginResponse)
async def login(
    response: Response,
    login_data: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    """
    이메일과 비밀번호로 로그인합니다.
    """
    user = crud.user.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 토큰 생성
    access_token = create_access_token(data={"sub": user.email, "id": user.id})
    refresh_token = create_refresh_token(data={"sub": user.email, "id": user.id})
    
    # 리프레시 토큰을 쿠키에 설정
    secure = os.getenv("ENVIRONMENT", "development") == "production"
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure,  # HTTPS에서만 전송
        samesite="lax" if secure else "none",  # CSRF 보호
        max_age=60 * 60 * 24 * 7,  # 7일
    )
    
    # 응답 헤더에 액세스 토큰 설정
    response.headers["Authorization"] = f"Bearer {access_token}"
    
    return schemas.LoginResponse(
        user=schemas.UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at
        ),
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/kakao", response_model=schemas.LoginResponse)
async def kakao_login(
    response: Response,
    login_req: schemas.KakaoLoginRequest,
    db: Session = Depends(get_db)
):
    """
    카카오 인증 코드로 로그인합니다.
    """
    login_response = await process_kakao_login(login_req.code, db)
    
    # 리프레시 토큰을 쿠키에 설정
    secure = os.getenv("ENVIRONMENT", "development") == "production"
    response.set_cookie(
        key="refresh_token",
        value=login_response.refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,  # 30일
        path="/auth/refresh"
    )
    
    return login_response

@router.get("/kakao")
async def kakao_login(
    success_uri: str = Query(...),
    error_uri: str = Query(...)
):
    """
    카카오 로그인 페이지로 리다이렉트합니다.
    성공/실패 시 리다이렉트할 URI를 state 파라미터로 전달합니다.
    """
    # 성공 및 에러 URI를 base64로 인코딩하여 state 파라미터에 포함
    state_data = {
        "success_uri": success_uri,
        "error_uri": error_uri
    }
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
    
    # 카카오 로그인 페이지 URL 생성 (state 파라미터 포함)
    kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={KAKAO_CLIENT_ID}&redirect_uri={KAKAO_REDIRECT_URI}&response_type=code&state={state}"
    
    return RedirectResponse(url=kakao_auth_url)

@router.get("/kakao/callback")
async def kakao_callback(
    response: Response,
    code: str = Query(None),
    error: str = Query(None),
    state: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    카카오 로그인 콜백 처리.
    인증 코드를 받아 로그인 처리 후 프론트엔드로 토큰을 전달합니다.
    """
    # 디버깅을 위한 로그 출력
    logger = logging.getLogger("uvicorn")
    logger.info(f"Kakao callback received. Code: {code[:10]}... State: {state[:30]}...")
    
    # state에서 리다이렉트 URI 디코딩
    success_uri = "/"
    error_uri = "/error"
    
    if state:
        try:
            state_data = json.loads(base64.urlsafe_b64decode(state).decode())
            success_uri = state_data.get("success_uri", success_uri)
            error_uri = state_data.get("error_uri", error_uri)
            logger.info(f"Decoded state. Success URI: {success_uri}, Error URI: {error_uri}")
        except Exception as e:
            logger.error(f"Failed to decode state: {str(e)}")
            # state 디코딩 실패 시 기본값 사용
            pass
    
    # 오류가 있으면 에러 페이지로 리다이렉트
    if error:
        logger.error(f"Kakao error: {error}")
        error_message = urllib.parse.quote(error)
        return RedirectResponse(url=f"{error_uri}?error={error_message}")
    
    try:
        # 카카오 로그인 처리
        logger.info("Processing Kakao login...")
        login_response = await process_kakao_login(code, db)
        logger.info(f"Kakao login successful. User ID: {login_response.user.id}")
        
        # 리프레시 토큰을 쿠키에 설정
        secure = os.getenv("ENVIRONMENT", "development") == "production"
        response.set_cookie(
            key="refresh_token",
            value=login_response.refresh_token,
            httponly=True,
            secure=secure,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,  # 30일
            path="/auth/refresh"
        )
        
        # 성공 URI로 리다이렉트 (해시 프래그먼트를 사용하여 토큰 전달)
        redirect_url = f"{success_uri}#access_token={login_response.access_token}"
        logger.info(f"Redirecting to: {success_uri}#access_token=...")
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        # 상세한 오류 정보 로깅
        import traceback
        logger.error(f"Kakao login error: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 오류 발생 시 에러 페이지로 리다이렉트
        error_message = urllib.parse.quote(str(e))
        return RedirectResponse(url=f"{error_uri}?error={error_message}")

"""
로그아웃 엔드포인트
- 쿠키에서 리프레시 토큰 제거
"""
@router.post("/logout")
async def logout(response: Response):
    """
    로그아웃합니다. 리프레시 토큰 쿠키를 삭제합니다.
    """
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=os.getenv("ENVIRONMENT", "development") == "production",
        samesite="lax" if os.getenv("ENVIRONMENT", "development") == "production" else "none"
    )
    
    return {"message": "로그아웃되었습니다."}

@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    리프레시 토큰을 사용하여 새 액세스 토큰을 발급합니다.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="리프레시 토큰이 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 리프레시 토큰 검증
    payload = verify_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    user_id = payload.get("id") or payload.get("user_id")
    
    # 사용자 확인
    user = crud.get_user(db, user_id=user_id)
    if not user or user.email != username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 새 토큰 생성
    new_access_token = create_access_token(data={"sub": username, "id": user_id})
    new_refresh_token = create_refresh_token(data={"sub": username, "id": user_id})
    
    # 리프레시 토큰을 쿠키에 설정
    secure = os.getenv("ENVIRONMENT", "development") == "production"
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=secure,  # HTTPS에서만 전송
        samesite="lax" if secure else "none",  # CSRF 보호
        max_age=60 * 60 * 24 * 7,  # 7일
    )
    
    # 응답 헤더에 액세스 토큰 설정
    response.headers["Authorization"] = f"Bearer {new_access_token}"
    
    return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

"""
현재 로그인한 사용자 정보 조회
"""
@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

"""
사용자의 게임 히스토리 조회
    
미들웨어에서 설정한 사용자 정보를 사용하여 해당 사용자의 게임 목록 조회
"""
@router.get("/history", response_model=schemas.UserGameHistoryResponse)
def get_user_game_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.user.get_user_game_history(db=db, user_id=current_user.id)

"""
특정 게임의 상세 히스토리 조회
    
1. 사용자 인증 확인
2. 해당 사용자의 특정 게임 상세 정보 조회
3. 게임이 종료된 경우 정답도 함께 반환
"""
@router.get("/history/{game_id}", response_model=schemas.GameDetailHistoryResponse)
def get_game_detail_history(game_id: int, request: Request, db: Session = Depends(get_db)):
    # 미들웨어에서 설정한 사용자 정보 사용
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = request.state.user["id"]
    return crud.user.get_game_detail_history(db=db, user_id=user_id, game_id=game_id)

@router.get("/debug-token")
async def debug_token(request: Request):
    """
    토큰 디버깅을 위한 엔드포인트
    """
    auth_header = request.headers.get("Authorization", "")
    cookies = request.cookies
    
    token_info = {"valid": False, "payload": None, "error": None}
    
    # 헤더에서 토큰 추출
    access_token = None
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.replace("Bearer ", "")
    
    # 토큰 디코딩 시도
    if access_token:
        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
            token_info = {"valid": True, "payload": payload, "error": None}
        except Exception as e:
            token_info = {"valid": False, "payload": None, "error": str(e)}
    
    # 리프레시 토큰 정보
    refresh_token_info = {"valid": False, "payload": None, "error": None}
    refresh_token = cookies.get("refresh_token")
    
    if refresh_token:
        try:
            refresh_payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            refresh_token_info = {"valid": True, "payload": refresh_payload, "error": None}
        except Exception as e:
            refresh_token_info = {"valid": False, "payload": None, "error": str(e)}
    
    return {
        "auth_header": auth_header,
        "has_auth_header": bool(auth_header),
        "access_token_info": token_info,
        "has_refresh_token": "refresh_token" in cookies,
        "refresh_token_info": refresh_token_info,
        "cookies": {k: v for k, v in cookies.items() if k != "refresh_token"}  # 리프레시 토큰 값은 숨김
    } 