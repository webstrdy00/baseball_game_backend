from fastapi import HTTPException
from sqlalchemy.orm import Session
import json
from datetime import datetime, UTC
from typing import List, Dict, Optional, Any

from .. import models, schemas, utils
from ..tetris import tetris_utils  # 테트리스 게임 로직 유틸리티

def create_game(db: Session, game_req: schemas.CreateTetrisGameRequest, user=None):
    """
    새 테트리스 게임을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        game_req: 게임 생성 요청 데이터
        user: 로그인한 사용자 (선택적)
    """
    # 초기 보드 상태 생성 (빈 보드)
    width = game_req.width
    height = game_req.height
    board = [[0 for _ in range(width)] for _ in range(height)]
    board_state = json.dumps(board)
    
    # 첫 번째 블록과 다음 블록 생성
    current_piece = tetris_utils.generate_piece()
    next_piece = tetris_utils.generate_piece()
    
    # 새 게임 생성
    new_game = models.TetrisGame(
        status="ongoing",
        score=0,
        level=game_req.level,
        lines_cleared=0,
        board_state=board_state,
        current_piece=json.dumps(current_piece),
        next_piece=json.dumps(next_piece),
        user_id=user.id if user else None
    )
    
    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    
    return schemas.CreateTetrisGameResponse(
        game_id=new_game.id,
        width=width,
        height=height,
        level=new_game.level,
        message="새로운 테트리스 게임이 시작되었습니다."
    )

def get_game_status(db: Session, game_id: int):
    """
    게임 상태를 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        game_id: 게임 ID
    """
    # 게임 조회
    game = db.query(models.TetrisGame).filter(models.TetrisGame.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="게임을 찾을 수 없습니다.")
    
    # JSON 문자열을 파이썬 객체로 변환
    board = json.loads(game.board_state)
    current_piece = json.loads(game.current_piece) if game.current_piece else None
    next_piece = json.loads(game.next_piece) if game.next_piece else None
    held_piece = json.loads(game.held_piece) if hasattr(game, 'held_piece') and game.held_piece else None
    
    return schemas.TetrisGameStatusResponse(
        game_id=game.id,
        status=game.status,
        board=board,
        current_piece=current_piece,
        next_piece=next_piece,
        held_piece=held_piece,
        score=game.score,
        level=game.level,
        lines_cleared=game.lines_cleared,
        can_hold=getattr(game, 'can_hold', True)
    )

def make_move(db: Session, game_id: int, move_req: schemas.TetrisMoveRequest):
    """
    게임에서 이동을 수행합니다.
    
    Args:
        db: 데이터베이스 세션
        game_id: 게임 ID
        move_req: 이동 요청 데이터
    """
    # 게임 조회
    game = db.query(models.TetrisGame).filter(models.TetrisGame.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="게임을 찾을 수 없습니다.")
    
    # 게임이 진행 중인지 확인
    if game.status != "ongoing":
        raise HTTPException(
            status_code=400,
            detail=f"게임이 진행 중이 아닙니다. 현재 상태: {game.status}"
        )
    
    # 게임 상태 로드
    board = json.loads(game.board_state)
    current_piece = json.loads(game.current_piece)
    next_piece = json.loads(game.next_piece)
    held_piece = json.loads(game.held_piece) if hasattr(game, 'held_piece') and game.held_piece else None
    can_hold = getattr(game, 'can_hold', True)
    
    # 이동 처리
    result = tetris_utils.process_move(
        board, 
        current_piece, 
        move_req.move_type, 
        next_piece=next_piece, 
        held_piece=held_piece,
        can_hold=can_hold
    )
    
    # 이동 결과 적용
    if not result["success"]:
        return schemas.TetrisMoveResponse(
            success=False,
            board=board,
            current_piece=current_piece,
            next_piece=next_piece,
            held_piece=held_piece,
            score=game.score,
            level=game.level,
            lines_cleared=game.lines_cleared,
            status=game.status,
            can_hold=can_hold,
            message=result["message"]
        )
    
    # 이동 결과 업데이트
    board = result["board"]
    current_piece = result["current_piece"]
    next_piece = result["next_piece"]
    held_piece = result.get("held_piece", held_piece)
    can_hold = result.get("can_hold", can_hold)
    
    # 라인 클리어 처리
    line_clear_result = tetris_utils.check_line_clear(board)
    cleared_lines = line_clear_result["cleared_lines"]
    board = line_clear_result["board"]
    
    # 점수 및 레벨 업데이트
    score_update = tetris_utils.calculate_score(cleared_lines, game.level, move_req.move_type)
    game.score += score_update
    game.lines_cleared += len(cleared_lines)
    
    # 레벨 업데이트
    new_level = tetris_utils.calculate_level(game.lines_cleared)
    game.level = new_level
    
    # 게임 오버 체크
    if tetris_utils.check_game_over(board, current_piece):
        game.status = "game_over"
        game.ended_at = datetime.now(UTC)
        
        # 최고 점수 등록 (로그인한 사용자의 경우)
        if game.user_id:
            game_duration = (game.ended_at - game.created_at).seconds
            save_high_score(db, game.user_id, game.score, game.level, game.lines_cleared, game_duration)
    
    # 게임 상태 업데이트
    game.board_state = json.dumps(board)
    game.current_piece = json.dumps(current_piece)
    game.next_piece = json.dumps(next_piece)
    
    # held_piece와 can_hold 속성이 없는 경우 추가
    if not hasattr(game, 'held_piece'):
        game.held_piece = json.dumps(held_piece) if held_piece else None
    else:
        game.held_piece = json.dumps(held_piece) if held_piece else None
    
    if not hasattr(game, 'can_hold'):
        game.can_hold = can_hold
    else:
        game.can_hold = can_hold
    
    # 이동 기록 저장
    move = models.TetrisMove(
        game_id=game.id,
        move_type=move_req.move_type,
        piece_position=json.dumps(current_piece["position"]) if current_piece else None,
        score_after_move=game.score,
        lines_cleared=len(cleared_lines)
    )
    db.add(move)
    
    # 변경사항 저장
    db.commit()
    db.refresh(game)
    
    return schemas.TetrisMoveResponse(
        success=True,
        board=board,
        current_piece=current_piece,
        next_piece=next_piece,
        held_piece=held_piece,
        score=game.score,
        level=game.level,
        lines_cleared=game.lines_cleared,
        line_clear_count=len(cleared_lines),
        status=game.status,
        can_hold=can_hold,
        message="이동이 성공적으로 처리되었습니다."
    )

def pause_game(db: Session, game_id: int, pause_req: schemas.TetrisPauseRequest):
    """
    게임을 일시정지하거나 재개합니다.
    
    Args:
        db: 데이터베이스 세션
        game_id: 게임 ID
        pause_req: 일시정지 요청 데이터
    """
    # 게임 조회
    game = db.query(models.TetrisGame).filter(models.TetrisGame.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="게임을 찾을 수 없습니다.")
    
    # 게임이 이미 종료된 경우
    if game.status == "game_over":
        raise HTTPException(status_code=400, detail="이미 종료된 게임입니다.")
    
    # 상태 업데이트
    if pause_req.paused:
        game.status = "paused"
        message = "게임이 일시정지되었습니다."
    else:
        game.status = "ongoing"
        message = "게임이 재개되었습니다."
    
    db.commit()
    
    return schemas.TetrisPauseResponse(
        game_id=game.id,
        status=game.status,
        message=message
    )

def forfeit_game(db: Session, game_id: int):
    """
    게임을 포기하고 종료합니다.
    
    Args:
        db: 데이터베이스 세션
        game_id: 게임 ID
    """
    # 게임 조회
    game = db.query(models.TetrisGame).filter(models.TetrisGame.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="게임을 찾을 수 없습니다.")
    
    # 이미 종료된 게임인 경우
    if game.status == "game_over":
        raise HTTPException(status_code=400, detail="이미 종료된 게임입니다.")
    
    # 게임 종료 처리
    game.status = "game_over"
    game.ended_at = datetime.now(UTC)
    
    # 최고 점수 등록 (로그인한 사용자의 경우)
    if game.user_id:
        game_duration = (game.ended_at - game.created_at).seconds
        save_high_score(db, game.user_id, game.score, game.level, game.lines_cleared, game_duration)
    
    db.commit()
    
    return schemas.TetrisGameOverResponse(
        game_id=game.id,
        final_score=game.score,
        level_reached=game.level,
        lines_cleared=game.lines_cleared,
        game_duration=(game.ended_at - game.created_at).seconds,
        high_score=False  # 기본값, 최고 점수 여부는 save_high_score 함수에서 결정
    )

def save_high_score(db: Session, user_id: int, score: int, level: int, lines_cleared: int, game_duration: int):
    """
    사용자의 최고 점수를 저장합니다.
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        score: 게임 점수
        level: 도달한 레벨
        lines_cleared: 제거한 라인 수
        game_duration: 게임 지속 시간(초)
    """
    # 사용자의 기존 최고 점수 조회
    highest_score = db.query(models.TetrisHighScore).filter(
        models.TetrisHighScore.user_id == user_id
    ).order_by(models.TetrisHighScore.score.desc()).first()
    
    # 이번 점수가 기존 최고 점수보다 높거나, 최고 점수가 없는 경우
    if not highest_score or score > highest_score.score:
        new_high_score = models.TetrisHighScore(
            user_id=user_id,
            score=score,
            level=level,
            lines_cleared=lines_cleared,
            game_duration=game_duration
        )
        db.add(new_high_score)
        db.commit()
        return True
    
    return False

def get_leaderboard(db: Session, limit: int = 10):
    """
    최고 점수 리더보드를 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        limit: 조회할 최대 항목 수
    """
    # 최고 점수 목록 조회
    high_scores = db.query(
        models.TetrisHighScore,
        models.User.username
    ).join(
        models.User, models.TetrisHighScore.user_id == models.User.id
    ).order_by(
        models.TetrisHighScore.score.desc()
    ).limit(limit).all()
    
    # 결과 변환
    leaderboard = []
    for high_score, username in high_scores:
        leaderboard.append(
            schemas.TetrisHighScoreItem(
                username=username,
                score=high_score.score,
                level=high_score.level,
                lines_cleared=high_score.lines_cleared,
                game_duration=high_score.game_duration,
                created_at=high_score.created_at
            )
        )
    
    return schemas.TetrisLeaderboardResponse(scores=leaderboard)

def get_user_high_scores(db: Session, user_id: int, limit: int = 5):
    """
    사용자의 최고 점수 목록을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        limit: 조회할 최대 항목 수
    """
    # 사용자의 최고 점수 목록 조회
    high_scores = db.query(
        models.TetrisHighScore
    ).filter(
        models.TetrisHighScore.user_id == user_id
    ).order_by(
        models.TetrisHighScore.score.desc()
    ).limit(limit).all()
    
    # 사용자 정보 조회
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 결과 변환
    scores = []
    for high_score in high_scores:
        scores.append(
            schemas.TetrisHighScoreItem(
                username=user.username,
                score=high_score.score,
                level=high_score.level,
                lines_cleared=high_score.lines_cleared,
                game_duration=high_score.game_duration,
                created_at=high_score.created_at
            )
        )
    
    return schemas.TetrisLeaderboardResponse(scores=scores)