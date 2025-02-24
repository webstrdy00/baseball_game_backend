from sqlalchemy.orm import Session
from .. import models, schemas, utils

def create_game(db: Session, game_req: schemas.CreateGameRequest):
    random_num = utils.generate_random_number(game_req.digits)
    new_game = models.Game(
        random_number=random_num,
        digits=game_req.digits
    )
    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    
    return schemas.CreateGameResponse(
        game_id=new_game.id,
        message=f"새로운 {new_game.digits}자리 숫자 야구 게임이 시작되었습니다."
    )