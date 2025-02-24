from pydantic import BaseModel

# 게임 생성 시 요청 바디
class CreateGameRequest(BaseModel):
    digits: int = 3  # 기본값 3

# 게임 생성 후 응답 바디
class CreateGameResponse(BaseModel):
    game_id: int
    message: str    