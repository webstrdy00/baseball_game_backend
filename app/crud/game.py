from fastapi import HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, utils

MAX_ATTEMPTS = 10  # 최대 시도 횟수

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

def make_guess(db: Session, game_id: int, guess_req: schemas.GuessRequest):
    # 1. 게임 조회
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="게임을 찾을 수 없습니다.")
    
    # 2. 게임 상태 확인
    if game.status != "ongoing":
        raise HTTPException(
            status_code=400,
            detail=f"이미 종료된 게임입니다. 현재 상태: {game.status}"
        )
    
    # 3. 추측한 숫자의 자릿수 검증
    if len(guess_req.guess) != game.digits:
        raise HTTPException(
            status_code=400,
            detail=f"입력한 숫자의 자릿수가 {game.digits}와 일치하지 않습니다."
        )
    
    # 4. 스트라이크/볼 계산
    strike, ball = utils.calculate_strike_ball(game.random_number, guess_req.guess)
    
    # 5. 시도 횟수 증가 및 게임 상태 업데이트
    game.attempts_used += 1
    
    # 6. Guess 레코드 생성
    new_guess = models.Guess(
        game_id=game.id,
        guess=guess_req.guess,
        strike=strike,
        ball=ball
    )
    db.add(new_guess)
    
    # 7. 게임 상태 업데이트
    if strike == game.digits:
        game.status = "win"
        # 게임 종료 시 이전 기록 삭제
        delete_game_history(db, game_id)
    elif game.attempts_used >= MAX_ATTEMPTS:
        game.status = "lose"
        # 게임 종료 시 이전 기록 삭제
        delete_game_history(db, game_id)
    
    db.commit()
    
    # 8. 응답 정보 구성
    attempts_left = MAX_ATTEMPTS - game.attempts_used if game.status == "ongoing" else 0
    message = f"{strike} 스트라이크, {ball} 볼입니다."
    if game.status == "win":
        message = f"정답입니다! {game.attempts_used}번 만에 맞추셨습니다."
    elif game.status == "lose":
        message = f"기회를 모두 소진했습니다. 정답은 {game.random_number} 였습니다."
    
    return schemas.GuessResponse(
        strike=strike,
        ball=ball,
        attempts_used=game.attempts_used,
        attempts_left=attempts_left,
        status=game.status,
        message=message
    )

def delete_game_history(db: Session, game_id: int):
    """
    게임이 종료되면 해당 게임의 이전 추측 기록을 삭제합니다.
    """
    db.query(models.Guess).filter(models.Guess.game_id == game_id).delete()
    db.commit()

def get_game_status(db: Session, game_id: int):
    # 게임 조회
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="게임을 찾을 수 없습니다.")
    
    # Guess 테이블에서 해당 게임의 추측 내역을 생성 시각 순으로 조회
    guess_history = (
        db.query(models.Guess)
        .filter(models.Guess.game_id == game_id)
        .order_by(models.Guess.created_at.asc())
        .all()
    )
    
    history = []
    for guess in guess_history:
        history.append({
            "guess": guess.guess,
            "strike": guess.strike,
            "ball": guess.ball,
            "created_at": guess.created_at
        })
    
    # 진행 중인 경우 남은 시도 횟수를 계산
    attempts_left = MAX_ATTEMPTS - game.attempts_used if game.status == "ongoing" else 0

    return schemas.GameStatusResponse(
        game_id=game.id,
        attempts_used=game.attempts_used,
        attempts_left=attempts_left,
        status=game.status,
        history=history
    )