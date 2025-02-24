from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, schemas

router = APIRouter()

@router.post("/games", response_model=schemas.CreateGameResponse)
def create_game(game_req: schemas.CreateGameRequest, db: Session = Depends(get_db)):
    return crud.game.create_game(db=db, game_req=game_req)