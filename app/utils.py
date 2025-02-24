import random

def generate_random_number(digits: int = 3) -> str:
    """
    지정된 digits 수만큼 겹치지 않는 0~9 숫자를 랜덤 생성.
    예) digits=3 이면 "123" 형태 반환
    """
    # sample()을 쓰면 중복되지 않는 숫자들을 뽑을 수 있습니다.
    numbers = random.sample("0123456789", digits)
    # 0으로 시작해도 상관없다면 그대로 join, 
    # 만약 첫 자리가 0이면 안 된다고 하면 추가 로직을 넣을 수 있음.
    return "".join(numbers) 

def calculate_strike_ball(answer: str, guess: str) -> tuple[int, int]:
    """
    answer와 guess를 비교해 스트라이크/볼 개수를 계산한다.
    """
    strike = 0
    ball = 0
    for i in range(len(guess)):
        if guess[i] == answer[i]:
            strike += 1
        elif guess[i] in answer:
            ball += 1
    return strike, ball