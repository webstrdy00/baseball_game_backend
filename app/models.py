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
    hashed_password = Column(String, nullable=True)  # 소셜 로그인 사용자는 비밀번호가 없을 수 있음
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # 소셜 로그인 관련 필드 추가
    social_id = Column(String, nullable=True)  # 소셜 서비스에서의 사용자 ID
    social_type = Column(String, nullable=True)  # 소셜 서비스 타입 (kakao, google 등)
    
    # 관계 설정
    games = relationship("Game", back_populates="user")
    tetris_games = relationship("TetrisGame", back_populates="user")
    tetris_high_scores = relationship("TetrisHighScore", back_populates="user")

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

class TetrisGame(Base):
    __tablename__ = "tetris_games"

    id = Column(Integer, primary_key=True, index=True)
    # 게임 상태 (ongoing, paused, game_over)
    status = Column(String, default="ongoing")
    # 현재 점수
    score = Column(Integer, default=0)
    # 현재 레벨
    level = Column(Integer, default=1)
    # 제거한 라인 수
    lines_cleared = Column(Integer, default=0)
    # 게임 보드 상태 (JSON 형태로 저장)
    board_state = Column(String, default="{}")
    # 현재 블록 정보
    current_piece = Column(String, nullable=True)
    # 다음 블록 정보
    next_piece = Column(String, nullable=True)
    # 홀드된 블록 정보
    held_piece = Column(String, nullable=True)
    # 홀드 사용 가능 여부
    can_hold = Column(Boolean, default=True)
    # 게임 시작 시각
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    # 마지막 업데이트 시각
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    # 게임 종료 시각
    ended_at = Column(DateTime, nullable=True)
    # 사용자 ID (nullable - 로그인 없이도 게임 가능)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 관계 설정
    user = relationship("User", back_populates="tetris_games")
    moves = relationship("TetrisMove", back_populates="game", cascade="all, delete-orphan")

class TetrisMove(Base):
    __tablename__ = "tetris_moves"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("tetris_games.id"))
    # 이동 타입 (left, right, rotate, drop, hard_drop)
    move_type = Column(String, nullable=False)
    # 이동 후 블록 위치
    piece_position = Column(String, nullable=True)
    # 이동 후 점수
    score_after_move = Column(Integer, default=0)
    # 이동으로 제거된 라인 수
    lines_cleared = Column(Integer, default=0)
    # 이동 시각
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # 관계 설정
    game = relationship("TetrisGame", back_populates="moves")


# 테트리스 게임 점수 기록
class TetrisHighScore(Base):
    __tablename__ = "tetris_high_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Integer, default=0)
    level = Column(Integer, default=1)
    lines_cleared = Column(Integer, default=0)
    game_duration = Column(Integer, default=0)  # 초 단위
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # 관계 설정
    user = relationship("User", back_populates="tetris_high_scores")