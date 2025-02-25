from pydantic import BaseModel
from datetime import datetime
from typing import List

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
    attempts_used: int
    attempts_left: int
    status: str
    history: List[GuessHistory]

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

# 로그인 요청 스키마 추가
class LoginRequest(BaseModel):
    username: str
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