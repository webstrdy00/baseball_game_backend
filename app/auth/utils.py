from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from .. import models, schemas, crud
from ..database import get_db
from typing import Optional, Dict, Any

# .env 파일 로드
load_dotenv()

# 환경 변수에서 설정 가져오기
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# 비밀번호 해싱 도구
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OAuth2 인증 스키마 (Swaager UI에서 인증 버튼 표시)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    액세스 토큰 생성
    
    Args:
        data: 토큰에 포함할 데이터
        expires_delta: 만료 시간 (없으면 기본값 사용)
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """
    리프레시 토큰 생성 (액세스 토큰보다 긴 유효기간)
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    토큰에서 현재 사용자 정보를 추출하는 의존성 함수
    (FastAPI의 Depends를 통해 사용)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 토큰 디코딩 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")  # username 대신 email
        user_id: int = payload.get("id")
        if email is None or user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=email, user_id=user_id)  # 여기서는 username 필드를 그대로 사용
    except JWTError:
        raise credentials_exception
    
    # DB에서 사용자 조회 - 이메일로 변경
    user = db.query(models.User).filter(models.User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user

# 선택적 인증 - 로그인 없이도 게임 가능하게 함
def get_optional_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    선택적 인증을 위한 의존성 함수
    토큰이 없거나 유효하지 않으면 None 반환
    """
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            return None
        
        user = db.query(models.User).filter(models.User.id == user_id).first()
        return user
    except:
        return None

# 미들웨어에서 설정한 사용자 정보 가져오기
def get_current_user_from_request(request: Request, db: Session = Depends(get_db)):
    """
    미들웨어에서 설정한 사용자 정보를 가져오는 의존성 함수
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 정보가 유효하지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_data = request.state.user
    user = db.query(models.User).filter(models.User.id == user_data["id"]).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# 선택적 인증 - 로그인 없이도 게임 가능하게 함
def get_optional_current_user_from_request(request: Request, db: Session = Depends(get_db)):
    """
    미들웨어에서 설정한 사용자 정보를 선택적으로 가져오는 의존성 함수
    사용자 정보가 없으면 None 반환
    """
    if not hasattr(request.state, "user"):
        return None
    
    user_data = request.state.user
    user = db.query(models.User).filter(models.User.id == user_data["id"]).first()
    return user 

# 쿠키에서 토큰 추출하는 함수 추가
def get_token_from_cookie(request: Request):
    """쿠키에서 액세스 토큰 추출"""
    return request.cookies.get("access_token")

# 쿠키 기반 인증 의존성 함수
def get_current_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    쿠키에서 토큰을 추출하여 사용자 인증
    """
    token = get_token_from_cookie(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 정보가 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 정보",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user 

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    JWT 토큰을 검증합니다.
    
    Args:
        token: 검증할 JWT 토큰
        
    Returns:
        검증 성공 시 토큰의 페이로드, 실패 시 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None 