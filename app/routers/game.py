from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models,crud, schemas
from ..auth.utils import get_optional_current_user

router = APIRouter()

"""
새 게임 생성 엔드포인트
    
1. 선택적 인증 - 로그인한 경우 사용자 정보 활용
2. 게임 생성 및 응답 반환
"""
@router.post("/games", response_model=schemas.CreateGameResponse)
def create_game(
    game_req: schemas.CreateGameRequest, 
    request: Request,
    db: Session = Depends(get_db)
):
    # 미들웨어에서 설정한 사용자 정보 사용 (선택적)
    user = None
    if hasattr(request.state, "user"):
        user_id = request.state.user["id"]
        user = db.query(models.User).filter(models.User.id == user_id).first()
    
    return crud.game.create_game(db=db, game_req=game_req, user=user)

"""
게임에 숫자 추측 엔드포인트
    
1. 게임 ID와 추측 숫자를 받아 처리
2. 스트라이크/볼 계산 및 게임 상태 업데이트
3. 결과 응답 반환
"""
@router.post("/games/{game_id}/guesses", response_model=schemas.GuessResponse)
def make_guess(game_id: int, guess_req: schemas.GuessRequest, db: Session = Depends(get_db)):
    return crud.game.make_guess(db=db, game_id=game_id, guess_req=guess_req)

"""
게임 상태 조회 엔드포인트
    
1. 게임 ID로 게임 정보 조회
2. 게임 상태 및 추측 내역 반환
"""
@router.get("/games/{game_id}", response_model=schemas.GameStatusResponse)
def get_game_status(game_id: int, db: Session = Depends(get_db)):
    return crud.game.get_game_status(db=db, game_id=game_id)

"""
게임 포기 엔드포인트
    
1. 게임 ID로 게임 조회
2. 게임 상태를 포기(forfeited)로 변경
3. 결과 응답 반환
"""
@router.delete("/games/{game_id}", response_model=schemas.ForfeitResponse)
def forfeit_game(game_id: int, db: Session = Depends(get_db)):
    return crud.game.forfeit_game(db=db, game_id=game_id)