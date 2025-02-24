from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, schemas

router = APIRouter()

@router.post("/games", response_model=schemas.CreateGameResponse)
def create_game(game_req: schemas.CreateGameRequest, db: Session = Depends(get_db)):
    return crud.game.create_game(db=db, game_req=game_req)

@router.post("/games/{game_id}/guesses", response_model=schemas.GuessResponse)
def make_guess(game_id: int, guess_req: schemas.GuessRequest, db: Session = Depends(get_db)):
    return crud.game.make_guess(db=db, game_id=game_id, guess_req=guess_req)