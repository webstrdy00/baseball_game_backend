import random
from typing import List, Dict, Any, Optional
import copy

# 테트리스 블록 정의
SHAPES = {
    "I": {
        "shape": [
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ],
        "color": 1  # 색상 코드
    },
    "J": {
        "shape": [
            [2, 0, 0],
            [2, 2, 2],
            [0, 0, 0]
        ],
        "color": 2
    },
    "L": {
        "shape": [
            [0, 0, 3],
            [3, 3, 3],
            [0, 0, 0]
        ],
        "color": 3
    },
    "O": {
        "shape": [
            [4, 4],
            [4, 4]
        ],
        "color": 4
    },
    "S": {
        "shape": [
            [0, 5, 5],
            [5, 5, 0],
            [0, 0, 0]
        ],
        "color": 5
    },
    "T": {
        "shape": [
            [0, 6, 0],
            [6, 6, 6],
            [0, 0, 0]
        ],
        "color": 6
    },
    "Z": {
        "shape": [
            [7, 7, 0],
            [0, 7, 7],
            [0, 0, 0]
        ],
        "color": 7
    }
}

def generate_piece():
    """
    새로운 테트리스 블록을 생성합니다.
    """
    piece_type = random.choice(list(SHAPES.keys()))
    piece = {
        "type": piece_type,
        "shape": copy.deepcopy(SHAPES[piece_type]["shape"]),
        "color": SHAPES[piece_type]["color"],
        "position": [0, 3],  # 시작 위치 (맨 위 중앙)
        "rotation": 0
    }
    return piece

def rotate_piece(piece):
    """
    블록을 시계방향으로 90도 회전합니다.
    """
    shape = piece["shape"]
    N = len(shape)
    rotated = [[0 for _ in range(N)] for _ in range(N)]
    
    # 시계방향 90도 회전
    for i in range(N):
        for j in range(N):
            rotated[j][N-1-i] = shape[i][j]
    
    new_piece = copy.deepcopy(piece)
    new_piece["shape"] = rotated
    new_piece["rotation"] = (piece["rotation"] + 1) % 4
    return new_piece

def check_collision(board, piece, offset=(0, 0)):
    """
    블록이 보드와 충돌하는지 확인합니다.
    
    Args:
        board: 게임 보드
        piece: 테트리스 블록
        offset: (row_offset, col_offset) 형태의 오프셋
    
    Returns:
        bool: 충돌하면 True, 아니면 False
    """
    shape = piece["shape"]
    pos_row, pos_col = piece["position"]
    off_row, off_col = offset
    
    for i in range(len(shape)):
        for j in range(len(shape[i])):
            if shape[i][j] == 0:  # 빈 공간은 무시
                continue
                
            row = pos_row + i + off_row
            col = pos_col + j + off_col
            
            # 보드 바깥으로 나가는 경우
            if row < 0 or row >= len(board) or col < 0 or col >= len(board[0]):
                return True
            
            # 보드에 이미 블록이 있는 경우
            if board[row][col] != 0:
                return True
    
    return False

def merge_piece_to_board(board, piece):
    """
    블록을 보드에 병합합니다.
    """
    shape = piece["shape"]
    pos_row, pos_col = piece["position"]
    color = piece["color"]
    
    new_board = copy.deepcopy(board)
    
    for i in range(len(shape)):
        for j in range(len(shape[i])):
            if shape[i][j] == 0:  # 빈 공간은 무시
                continue
                
            row = pos_row + i
            col = pos_col + j
            
            # 보드 범위 내에 있는 경우에만 병합
            if 0 <= row < len(board) and 0 <= col < len(board[0]):
                new_board[row][col] = color
    
    return new_board

def check_line_clear(board):
    """
    완성된 라인을 확인하고 제거합니다.
    
    Returns:
        dict: {"board": 업데이트된 보드, "cleared_lines": 제거된 라인 인덱스 목록}
    """
    new_board = copy.deepcopy(board)
    cleared_lines = []
    
    for i in range(len(board)):
        if all(cell != 0 for cell in board[i]):
            cleared_lines.append(i)
    
    # 라인 제거 및 위에서 블록 내려오기
    if cleared_lines:
        # 제거된 라인 수만큼 맨 위에 빈 라인 추가
        for line in cleared_lines:
            new_board.pop(line)
            new_board.insert(0, [0 for _ in range(len(board[0]))])
    
    return {
        "board": new_board,
        "cleared_lines": cleared_lines
    }

def calculate_score(cleared_lines, level, move_type):
    """
    제거된 라인 수와 레벨에 따라 점수를 계산합니다.
    """
    if not cleared_lines:
        return 0
    
    # 기본 점수표
    line_scores = {
        1: 100,  # 1줄: 100점
        2: 300,  # 2줄: 300점
        3: 500,  # 3줄: 500점
        4: 800   # 4줄(테트리스): 800점
    }
    
    # 하드 드롭 보너스
    hard_drop_bonus = 0
    if move_type == "hard_drop":
        hard_drop_bonus = 20 * level
    
    # 기본 점수 계산
    base_score = line_scores.get(len(cleared_lines), 100 * len(cleared_lines))
    
    # 레벨에 따른 배수 적용
    return base_score * level + hard_drop_bonus

def calculate_level(lines_cleared):
    """
    제거한 총 라인 수에 따라 레벨을 계산합니다.
    """
    return lines_cleared // 10 + 1

def process_move(board, current_piece, move_type, next_piece=None, held_piece=None, can_hold=True):
    """
    이동을 처리하고 결과를 반환합니다.
    
    Args:
        board: 게임 보드
        current_piece: 현재 블록
        move_type: 이동 타입
        next_piece: 다음 블록 (선택적)
        held_piece: 보관 중인 블록 (선택적)
        can_hold: 현재 홀드 가능 여부
    
    Returns:
        dict: 이동 결과 정보
    """
    result = {
        "success": False,
        "message": "",
        "board": board,
        "current_piece": current_piece,
        "next_piece": next_piece,
        "held_piece": held_piece,
        "can_hold": can_hold
    }
    
    # 이동 처리
    if move_type == "left":
        # 왼쪽 이동
        if not check_collision(board, current_piece, (0, -1)):
            current_piece["position"][1] -= 1
            result["success"] = True
        else:
            result["message"] = "왼쪽으로 이동할 수 없습니다."
    
    elif move_type == "right":
        # 오른쪽 이동
        if not check_collision(board, current_piece, (0, 1)):
            current_piece["position"][1] += 1
            result["success"] = True
        else:
            result["message"] = "오른쪽으로 이동할 수 없습니다."
    
    elif move_type == "down":
        # 아래로 이동
        if not check_collision(board, current_piece, (1, 0)):
            current_piece["position"][0] += 1
            result["success"] = True
        else:
            # 더 이상 내려갈 수 없으면 보드에 병합
            result["board"] = merge_piece_to_board(board, current_piece)
            
            # 다음 블록 설정
            if next_piece:
                result["current_piece"] = next_piece
                result["next_piece"] = generate_piece()
                result["success"] = True
            else:
                result["message"] = "게임이 종료되었습니다."
    
    elif move_type == "rotate":
        # 회전
        rotated_piece = rotate_piece(current_piece)
        if not check_collision(board, rotated_piece):
            result["current_piece"] = rotated_piece
            result["success"] = True
        else:
            # 벽 밀기 (wall kick) 시도
            offsets = [(0, -1), (0, 1), (-1, 0), (1, 0)]
            for off_row, off_col in offsets:
                rotated_piece_with_offset = copy.deepcopy(rotated_piece)
                rotated_piece_with_offset["position"][0] += off_row
                rotated_piece_with_offset["position"][1] += off_col
                
                if not check_collision(board, rotated_piece_with_offset):
                    result["current_piece"] = rotated_piece_with_offset
                    result["success"] = True
                    break
            
            if not result["success"]:
                result["message"] = "회전할 수 없습니다."
    
    elif move_type == "drop":
        # 한 칸 드롭
        if not check_collision(board, current_piece, (1, 0)):
            current_piece["position"][0] += 1
            result["success"] = True
        else:
            # 더 이상 내려갈 수 없으면 보드에 병합
            result["board"] = merge_piece_to_board(board, current_piece)
            
            # 다음 블록 설정
            if next_piece:
                result["current_piece"] = next_piece
                result["next_piece"] = generate_piece()
                result["success"] = True
            else:
                result["message"] = "게임이 종료되었습니다."
    
    elif move_type == "hard_drop":
        # 하드 드롭 (최대한 아래로)
        rows_dropped = 0
        while not check_collision(board, current_piece, (rows_dropped + 1, 0)):
            rows_dropped += 1
        
        # 위치 업데이트
        current_piece["position"][0] += rows_dropped
        
        # 보드에 병합
        result["board"] = merge_piece_to_board(board, current_piece)
        
        # 다음 블록 설정
        if next_piece:
            result["current_piece"] = next_piece
            result["next_piece"] = generate_piece()
            result["success"] = True
        else:
            result["message"] = "게임이 종료되었습니다."
    
    elif move_type == "hold":
        # 홀드 기능
        if can_hold:
            if held_piece:
                # 보관된 블록과 현재 블록 교체
                temp = current_piece
                result["current_piece"] = held_piece
                result["held_piece"] = temp
            else:
                # 현재 블록을 보관하고 다음 블록을 현재 블록으로 설정
                result["held_piece"] = current_piece
                result["current_piece"] = next_piece
                result["next_piece"] = generate_piece()
            
            # 보관된 블록 위치 초기화
            result["held_piece"]["position"] = [0, 3]
            result["current_piece"]["position"] = [0, 3]
            result["can_hold"] = False  # 한 번 사용하면 피스가 설치될 때까지 사용 불가
            result["success"] = True
        else:
            result["message"] = "이미 홀드를 사용했습니다."
    
    return result

def check_game_over(board, current_piece):
    """
    게임 오버 상태를 확인합니다.
    """
    # 새 블록을 놓을 수 없는 경우 게임 오버
    return check_collision(board, current_piece)