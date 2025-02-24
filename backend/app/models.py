from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    # 게임에서 사용할 난수 (예: "123" 형태)
    random_number = Column(String, nullable=False)
    # 자릿수 (기본 3자리)
    digits = Column(Integer, default=3)
    # 게임 상태 (ongoing, win, lose 등)
    status = Column(String, default="ongoing")
    # 시도 횟수
    attempts_used = Column(Integer, default=0)
    # 생성 시각
    created_at = Column(DateTime, default=datetime.utcnow)
