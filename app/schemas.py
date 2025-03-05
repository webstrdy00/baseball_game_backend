from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum

# 사용자 관련 스키마
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

# 로그인 요청 스키마
class LoginRequest(BaseModel):
    email: str  # username에서 email로 변경
    password: str

# 로그인 응답 스키마 추가
class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
    model_config = {
        "from_attributes": True
    }

# 토큰 관련 스키마
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: str | None = None
    user_id: int | None = None
    
# 게임 생성 시 요청 바디
class CreateGameRequest(BaseModel):
    digits: int = 3  # 기본값 3

# 게임 생성 후 응답 바디
class CreateGameResponse(BaseModel):
    game_id: int
    message: str    

class GuessRequest(BaseModel):
    guess: str

class GuessResponse(BaseModel):
    strike: int
    ball: int
    attempts_used: int
    attempts_left: int
    status: str
    message: str

class GuessHistory(BaseModel):
    guess: str
    strike: int
    ball: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class GameStatusResponse(BaseModel):
    game_id: int
    digits: int
    attempts_used: int
    attempts_left: int
    status: str
    history: List[GuessHistory]
    answer: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class ForfeitResponse(BaseModel):
    message: str
    status: str  # 예: "forfeited"

    model_config = {
        "from_attributes": True
    }

# 사용자 게임 히스토리 스키마
class GameHistoryItem(BaseModel):
    game_id: int
    digits: int
    status: str
    attempts_used: int
    created_at: datetime
    last_guess: str | None = None
    last_guess_time: datetime | None = None

    model_config = {
        "from_attributes": True
    }

class UserGameHistoryResponse(BaseModel):
    username: str
    total_games: int
    games: List[GameHistoryItem]

    model_config = {
        "from_attributes": True
    }

# 게임 상세 히스토리 스키마
class GameGuessHistoryItem(BaseModel):
    guess: str
    strike: int
    ball: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class GameDetailHistoryResponse(BaseModel):
    game_id: int
    digits: int
    status: str
    attempts_used: int
    created_at: datetime
    guesses: List[GameGuessHistoryItem]
    answer: str | None = None

    model_config = {
        "from_attributes": True
    }

# 테트리스 블록 타입 정의
class TetrisPieceType(str, Enum):
    I = "I"  # I 블록
    J = "J"  # J 블록
    L = "L"  # L 블록
    O = "O"  # O 블록 (사각형)
    S = "S"  # S 블록
    T = "T"  # T 블록
    Z = "Z"  # Z 블록

# 이동 타입 정의
class TetrisMoveType(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    DOWN = "down"
    ROTATE = "rotate"
    DROP = "drop"
    HARD_DROP = "hard_drop"
    HOLD = "hold"

# 게임 상태 정의
class TetrisGameStatus(str, Enum):
    ONGOING = "ongoing"
    PAUSED = "paused"
    GAME_OVER = "game_over"

# 테트리스 조각 정보
class TetrisPiece(BaseModel):
    type: str
    shape: List[List[int]]
    color: int
    position: List[int]  # 수정된 부분 - 단일 리스트로 변경
    rotation: int

# 게임 생성 요청
class CreateTetrisGameRequest(BaseModel):
    width: int = 10  # 기본 가로 크기
    height: int = 20  # 기본 세로 크기
    level: int = 1   # 시작 레벨

# 게임 생성 응답
class CreateTetrisGameResponse(BaseModel):
    game_id: int
    width: int
    height: int
    level: int
    message: str

# 게임 상태 응답
class TetrisGameStatusResponse(BaseModel):
    """
    테트리스 게임 상태 응답 스키마
    """
    game_id: int
    status: str
    board: List[List[int]]
    current_piece: Optional[Dict[str, Any]]
    next_piece: Optional[Dict[str, Any]]
    held_piece: Optional[Dict[str, Any]] = None  # 홀드된 블록 정보
    score: int
    level: int
    lines_cleared: int
    can_hold: bool = True  # 홀드 사용 가능 여부
    
    class Config:
        from_attributes = True

# 이동 요청
class TetrisMoveRequest(BaseModel):
    move_type: TetrisMoveType

# 이동 응답
class TetrisMoveResponse(BaseModel):
    """
    테트리스 게임 이동 응답 스키마
    """
    success: bool
    board: List[List[int]]
    current_piece: Optional[Dict[str, Any]]
    next_piece: Optional[Dict[str, Any]]
    held_piece: Optional[Dict[str, Any]] = None  # 홀드된 블록 정보
    score: int
    level: int
    lines_cleared: int
    line_clear_count: int = 0
    status: str
    can_hold: bool = True  # 홀드 사용 가능 여부
    message: str
    
    class Config:
        from_attributes = True

# 일시정지 요청
class TetrisPauseRequest(BaseModel):
    paused: bool  # True: 일시정지, False: 재개

# 일시정지 응답
class TetrisPauseResponse(BaseModel):
    game_id: int
    status: TetrisGameStatus
    message: str
    
    model_config = {
        "from_attributes": True
    }

# 게임 종료 응답
class TetrisGameOverResponse(BaseModel):
    game_id: int
    final_score: int
    level_reached: int
    lines_cleared: int
    game_duration: int  # 초 단위
    high_score: bool  # 사용자의 최고 점수인지 여부
    
    model_config = {
        "from_attributes": True
    }

# 최고 점수 항목
class TetrisHighScoreItem(BaseModel):
    username: str
    score: int
    level: int
    lines_cleared: int
    game_duration: int
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }

# 최고 점수 목록 응답
class TetrisLeaderboardResponse(BaseModel):
    scores: List[TetrisHighScoreItem]
    
    model_config = {
        "from_attributes": True
    }