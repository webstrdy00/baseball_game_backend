from pydantic import BaseModel
from datetime import datetime
from typing import List
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

    class Config:
        orm_mode = True

class GameStatusResponse(BaseModel):
    game_id: int
    attempts_used: int
    attempts_left: int
    status: str
    history: List[GuessHistory]

    class Config:
        orm_mode = True