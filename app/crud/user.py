from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from .. import models, schemas, utils
from ..auth.utils import get_password_hash, verify_password, create_access_token, create_refresh_token
from datetime import timedelta, datetime, UTC
import random
import string

"""사용자명으로 사용자 조회"""
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

"""이메일로 사용자 조회"""
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

"""
새 사용자 생성
    
1. 이메일 중복 확인
2. 사용자명 중복 확인   
3. 비밀번호 해싱
4. 사용자 생성 및 저장
"""
def create_user(db: Session, user: schemas.UserCreate):
    # 이메일 중복 확인
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
    
    # 사용자명 중복 확인
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="이미 사용 중인 사용자명입니다")
    
    # 비밀번호 해싱
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

"""
사용자 인증 - 이메일 기반으로 변경
    
1. 이메일로 사용자 조회
2. 비밀번호 검증
3. 성공 시 사용자 객체 반환, 실패 시 False 반환
"""
def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

"""
사용자 인증 토큰 생성
    
1. 액세스 토큰 생성 (짧은 유효기간)
2. 리프레시 토큰 생성 (긴 유효기간)
"""
def create_user_tokens(user):
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email, "id": user.id}
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

"""
사용자의 게임 히스토리 조회
    
1. 사용자 확인
2. 사용자의 모든 게임 조회 (최신순)
3. 각 게임의 마지막 추측 정보 포함
"""
def get_user_game_history(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    # 사용자의 모든 게임 조회 (최신순)
    games = (
        db.query(models.Game)
        .filter(models.Game.user_id == user_id)
        .order_by(models.Game.created_at.desc())
        .all()
    )
    
    # 게임 정보 변환
    game_history = []
    for game in games:
        # 각 게임의 마지막 추측 조회
        last_guess = (
            db.query(models.Guess)
            .filter(models.Guess.game_id == game.id)
            .order_by(models.Guess.created_at.desc())
            .first()
        )
        
        game_info = {
            "game_id": game.id,
            "digits": game.digits,
            "status": game.status,
            "attempts_used": game.attempts_used,
            "created_at": game.created_at,
            "last_guess": last_guess.guess if last_guess else None,
            "last_guess_time": last_guess.created_at if last_guess else None
        }
        game_history.append(game_info)
    
    return {
        "username": user.username,
        "total_games": len(games),
        "games": game_history
    }

"""
특정 게임의 상세 히스토리 조회
    
1. 사용자 확인
2. 게임 조회 및 사용자 소유 확인
3. 게임의 모든 추측 내역 조회
4. 게임이 종료된 경우 정답 포함
"""
def get_game_detail_history(db: Session, user_id: int, game_id: int):
    # 사용자 확인
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    # 게임 조회 및 사용자 소유 확인
    game = db.query(models.Game).filter(
        models.Game.id == game_id,
        models.Game.user_id == user_id
    ).first()
    
    if not game:
        raise HTTPException(status_code=404, detail="게임을 찾을 수 없거나 접근 권한이 없습니다")
    
    # 게임의 모든 추측 내역 조회
    guesses = (
        db.query(models.Guess)
        .filter(models.Guess.game_id == game_id)
        .order_by(models.Guess.created_at.asc())
        .all()
    )
    
    guess_history = []
    for guess in guesses:
        guess_info = {
            "guess": guess.guess,
            "strike": guess.strike,
            "ball": guess.ball,
            "created_at": guess.created_at
        }
        guess_history.append(guess_info)
    
    return {
        "game_id": game.id,
        "digits": game.digits,
        "status": game.status,
        "attempts_used": game.attempts_used,
        "created_at": game.created_at,
        "guesses": guess_history,
        "answer": game.random_number if game.status != "ongoing" else None
    }

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user_by_social_id(db: Session, social_id: str, social_type: str):
    """
    소셜 ID와 소셜 타입으로 사용자를 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        social_id: 소셜 서비스에서의 사용자 ID
        social_type: 소셜 서비스 타입 (예: "kakao")
        
    Returns:
        조회된 사용자 또는 None
    """
    return db.query(models.User).filter(
        models.User.social_id == social_id,
        models.User.social_type == social_type
    ).first()

def create_social_user(db: Session, user: schemas.SocialUserCreate):
    """
    소셜 로그인으로 새 사용자를 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        user: 생성할 사용자 정보
        
    Returns:
        생성된 사용자
    """
    # 랜덤한 비밀번호 생성 (32자)
    random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    hashed_password = get_password_hash(random_password)
    
    db_user = models.User(
        username=user.username,
        email=user.email,
        social_id=user.social_id,
        social_type=user.social_type,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user 