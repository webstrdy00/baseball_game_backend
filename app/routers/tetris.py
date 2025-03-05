from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, crud, schemas
from ..auth.utils import get_optional_current_user

router = APIRouter()

"""
새 테트리스 게임 생성 엔드포인트
"""
@router.post("/tetris", response_model=schemas.CreateTetrisGameResponse)
def create_game(
    game_req: schemas.CreateTetrisGameRequest, 
    request: Request,
    db: Session = Depends(get_db)
):
    # 미들웨어에서 설정한 사용자 정보 사용 (선택적)
    user = None
    if hasattr(request.state, "user"):
        user_id = request.state.user["id"]
        user = db.query(models.User).filter(models.User.id == user_id).first()
    
    return crud.tetris.create_game(db=db, game_req=game_req, user=user)

"""
테트리스 리더보드 조회 엔드포인트
"""
@router.get("/tetris/leaderboard", response_model=schemas.TetrisLeaderboardResponse)
def get_leaderboard(
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    return crud.tetris.get_leaderboard(db=db, limit=limit)

"""
사용자의 테트리스 최고 점수 조회 엔드포인트
"""
@router.get("/tetris/user/highscores", response_model=schemas.TetrisLeaderboardResponse)
def get_user_high_scores(
    request: Request,
    limit: int = 5, 
    db: Session = Depends(get_db)
):
    # 미들웨어에서 설정한 사용자 정보 사용
    if not hasattr(request.state, "user"):
        return schemas.TetrisLeaderboardResponse(scores=[])
    
    user_id = request.state.user["id"]
    return crud.tetris.get_user_high_scores(db=db, user_id=user_id, limit=limit)

"""
테트리스 게임 상태 조회 엔드포인트
"""
@router.get("/tetris/{game_id}", response_model=schemas.TetrisGameStatusResponse)
def get_game_status(
    game_id: int, 
    db: Session = Depends(get_db)
):
    return crud.tetris.get_game_status(db=db, game_id=game_id)

"""
테트리스 게임 이동 엔드포인트
"""
@router.post("/tetris/{game_id}/moves", response_model=schemas.TetrisMoveResponse)
def make_move(
    game_id: int, 
    move_req: schemas.TetrisMoveRequest, 
    db: Session = Depends(get_db)
):
    return crud.tetris.make_move(db=db, game_id=game_id, move_req=move_req)

"""
테트리스 게임 일시정지/재개 엔드포인트
"""
@router.post("/tetris/{game_id}/pause", response_model=schemas.TetrisPauseResponse)
def pause_game(
    game_id: int, 
    pause_req: schemas.TetrisPauseRequest, 
    db: Session = Depends(get_db)
):
    return crud.tetris.pause_game(db=db, game_id=game_id, pause_req=pause_req)

"""
테트리스 게임 포기 엔드포인트
"""
@router.delete("/tetris/{game_id}", response_model=schemas.TetrisGameOverResponse)
def forfeit_game(
    game_id: int, 
    db: Session = Depends(get_db)
):
    return crud.tetris.forfeit_game(db=db, game_id=game_id)