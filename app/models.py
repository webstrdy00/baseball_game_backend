from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from .database import Base

"""
사용자 모델
    
- 사용자 인증 정보 저장
- 게임과 1:N 관계 설정
"""
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # 관계 설정
    games = relationship("Game", back_populates="user")

"""
게임 모델
    
- 게임 정보 저장
- 사용자와 N:1 관계
- 추측과 1:N 관계
"""
class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    # 게임에서 사용할 난수 (예: "123" 형태)
    random_number = Column(String, nullable=False)
    # 자릿수 (기본 3자리)
    digits = Column(Integer, default=3)
    # 게임 상태 (ongoing, win, lose 등)
    status = Column(String, default="ongoing")
    # 시도 횟수
    attempts_used = Column(Integer, default=0)
    # 생성 시각
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    # 사용자 ID (nullable - 로그인 없이도 게임 가능)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 관계 설정
    user = relationship("User", back_populates="games")
    guesses = relationship("Guess", back_populates="game")

"""
추측 모델
    
- 게임 내 각 추측 정보 저장
- 게임과 N:1 관계
"""
class Guess(Base):
    __tablename__ = "guesses"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    guess = Column(String, nullable=False)  # 예: "123"
    strike = Column(Integer, default=0)
    ball = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # 관계 설정
    game = relationship("Game", back_populates="guesses")