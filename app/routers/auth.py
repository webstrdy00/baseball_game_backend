from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from .. import models, crud, schemas
from ..database import get_db
from ..auth.utils import SECRET_KEY, ALGORITHM, get_current_user
from datetime import datetime, timedelta, UTC

router = APIRouter()

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
- 일반 JSON 요청으로 로그인
- 액세스 토큰은 헤더에 설정
- 리프레시 토큰은 쿠키에 설정
"""
@router.post("/login", response_model=schemas.LoginResponse)
def login(login_req: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = crud.user.authenticate_user(db, login_req.email, login_req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="잘못된 이메일 또는 비밀번호입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 토큰 생성
    tokens = crud.user.create_user_tokens(user)
    
    # 리프레시 토큰만 쿠키에 설정 (HttpOnly 쿠키)
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        # secure=True,  # HTTPS 적용 시 주석 해제
        samesite="lax",  # CSRF 보호
        max_age=7*24*3600,  # 7일
        path="/"
    )
    
    # 헤더에 액세스 토큰 설정
    response.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    
    # 응답 구성
    return {
        "user": user,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": tokens["token_type"]
    }

"""
로그아웃 엔드포인트
- 쿠키에서 리프레시 토큰 제거
"""
@router.post("/logout")
def logout(response: Response):
    # 쿠키에서 리프레시 토큰 제거
    response.delete_cookie(key="refresh_token", path="/")
    
    return {"message": "로그아웃 되었습니다"}

@router.post("/refresh", response_model=schemas.Token)
def refresh_token(token: schemas.Token, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자를 찾을 수 없습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return crud.user.create_user_tokens(user)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

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