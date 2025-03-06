from fastapi import HTTPException
from sqlalchemy.orm import Session
import json
from datetime import datetime, UTC
from typing import List, Dict, Optional, Any

from .. import models, schemas, utils
from ..tetris import tetris_utils  # 테트리스 게임 로직 유틸리티
from ..schemas import TetrisMoveType, TetrisGameStatus
import random

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
    
    # 새 게임 생성 - 데이터베이스에 컬럼이 있는지 확인하고 안전하게 초기화
    try:
        new_game = models.TetrisGame(
            status="ongoing",
            score=0,
            level=game_req.level,
            lines_cleared=0,
            board_state=board_state,
            current_piece=json.dumps(current_piece),
            next_piece=json.dumps(next_piece),
            held_piece=None,  # 초기에는 홀드된 블록 없음
            can_hold=True,    # 초기에는 홀드 가능
            user_id=user.id if user else None
        )
    except Exception as e:
        # 데이터베이스에 컬럼이 없는 경우 held_piece와 can_hold 필드 제외
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
    
    try:
        db.commit()
        db.refresh(new_game)
    except Exception as e:
        db.rollback()
        # 데이터베이스 오류 로깅
        print(f"데이터베이스 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="게임 생성 중 오류가 발생했습니다.")
    
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
    
    # 게임 상태 로드
    board = json.loads(game.board_state)
    current_piece = json.loads(game.current_piece) if game.current_piece else None
    next_piece = json.loads(game.next_piece) if game.next_piece else None
    held_piece = json.loads(game.held_piece) if game.held_piece else None
    can_hold = game.can_hold if hasattr(game, 'can_hold') else True
    
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
        can_hold=can_hold
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
    
    # held_piece와 can_hold 속성 안전하게 로드
    # 데이터베이스에 컬럼이 없는 경우를 대비한 예외 처리
    try:
        held_piece = json.loads(game.held_piece) if game.held_piece else None
    except (AttributeError, TypeError):
        held_piece = None
    
    try:
        can_hold = game.can_hold
    except AttributeError:
        can_hold = True
    
    # 이동 처리 - clear_hold와 skip_store 파라미터 추가
    result = tetris_utils.process_move(
        board, 
        current_piece, 
        move_req.move_type, 
        next_piece=next_piece, 
        held_piece=held_piece,
        can_hold=can_hold,
        clear_hold=move_req.clear_hold,
        skip_store=move_req.skip_store
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
    
    # held_piece와 can_hold 값을 항상 결과에서 가져오도록 수정
    # 결과에 없는 경우 기존 값 유지
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
    
    # held_piece와 can_hold 속성 안전하게 업데이트
    try:
        game.held_piece = json.dumps(held_piece) if held_piece else None
    except AttributeError:
        # 데이터베이스에 컬럼이 없는 경우 처리
        pass
    
    try:
        game.can_hold = can_hold
    except AttributeError:
        # 데이터베이스에 컬럼이 없는 경우 처리
        pass
    
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

# 테트리스 블록 생성 함수
def generate_new_piece():
    # 블록 생성 로직...
    pass

# 게임 상태 업데이트 함수
def update_game_state(db: Session, game_id: int, move_req: schemas.TetrisMoveRequest):
    game = db.query(models.TetrisGame).filter(models.TetrisGame.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="게임을 찾을 수 없습니다.")
    
    # 게임 상태 확인
    if game.status != "ongoing":
        raise HTTPException(status_code=400, detail=f"진행 중인 게임이 아닙니다. 현재 상태: {game.status}")
    
    # 현재 게임 상태 로드
    board = json.loads(game.board_state)
    current_piece = json.loads(game.current_piece) if game.current_piece else None
    next_piece = json.loads(game.next_piece) if game.next_piece else None
    held_piece = json.loads(game.held_piece) if game.held_piece else None
    can_hold = game.can_hold if hasattr(game, 'can_hold') else True
    
    # 이동 처리
    success = True
    line_clear_count = 0
    message = "이동이 성공적으로 처리되었습니다."
    
    if move_req.move_type == TetrisMoveType.HOLD:
        if can_hold:
            # 홀드 로직 - 프론트엔드 요구사항에 맞게 수정
            if held_piece:
                # 홀드된 블록이 있는 경우
                if move_req.clear_hold and move_req.skip_store:
                    # 홀드된 블록을 현재 블록으로 가져오고, 홀드 공간은 비우기
                    current_piece = held_piece
                    held_piece = None
                elif move_req.clear_hold:
                    # 홀드된 블록을 현재 블록으로 가져오고, 현재 블록을 홀드에 저장
                    current_piece, held_piece = held_piece, current_piece
                elif move_req.skip_store:
                    # 홀드된 블록을 현재 블록으로 가져오고, 현재 블록은 저장하지 않음
                    current_piece = held_piece
                    # held_piece는 변경하지 않음
                else:
                    # 기본 동작: 홀드된 블록과 현재 블록 교체
                    current_piece, held_piece = held_piece, current_piece
            else:
                # 홀드된 블록이 없는 경우 (첫 홀드)
                if move_req.skip_store:
                    # 현재 블록을 홀드에 저장하지 않고, 다음 블록을 현재 블록으로
                    current_piece = next_piece
                    next_piece = tetris_utils.generate_piece()
                    # held_piece는 변경하지 않음 (None 유지)
                else:
                    # 기본 동작: 현재 블록을 홀드하고 새 블록 생성
                    held_piece = current_piece
                    current_piece = next_piece
                    next_piece = tetris_utils.generate_piece()
            
            # 홀드 사용 표시
            can_hold = False
            message = "블록이 홀드되었습니다."
        else:
            success = False
            message = "이미 홀드를 사용했습니다."
    
    elif move_req.move_type in [TetrisMoveType.LEFT, TetrisMoveType.RIGHT, TetrisMoveType.DOWN, TetrisMoveType.ROTATE]:
        # 일반 이동 로직
        # ...
        pass
    
    elif move_req.move_type == TetrisMoveType.DROP or move_req.move_type == TetrisMoveType.HARD_DROP:
        # 드롭 로직
        # ...
        
        # 블록이 바닥에 닿았을 때
        # 보드에 블록 고정
        # ...
        
        # 라인 클리어 체크
        # ...
        
        # 중요: 새 블록 생성 시에도 held_piece 정보 유지
        current_piece = next_piece
        next_piece = tetris_utils.generate_piece()
        
        # 홀드 사용 가능하도록 리셋
        can_hold = True
        
        # 게임 오버 체크
        # ...
    
    # 게임 상태 업데이트
    game.board_state = json.dumps(board)
    game.current_piece = json.dumps(current_piece)
    game.next_piece = json.dumps(next_piece)
    game.held_piece = json.dumps(held_piece) if held_piece else None  # 홀드된 블록 정보 항상 저장
    
    # can_hold 필드가 있는 경우에만 업데이트
    if hasattr(game, 'can_hold'):
        game.can_hold = can_hold
    
    # 점수, 레벨 등 업데이트
    # ...
    
    game.updated_at = datetime.now(UTC)
    db.commit()
    
    # 응답 반환 - 항상 held_piece 포함
    return schemas.TetrisMoveResponse(
        success=success,
        board=board,
        current_piece=current_piece,
        next_piece=next_piece,
        held_piece=held_piece,  # 항상 held_piece 정보 포함
        score=game.score,
        level=game.level,
        lines_cleared=game.lines_cleared,
        line_clear_count=line_clear_count,
        status=game.status,
        can_hold=can_hold,
        message=message
    )