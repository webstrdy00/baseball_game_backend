from sqlalchemy import Column, Integer, String, DateTime
from .database import Base
import datetime

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    answer = Column(String)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String)  # 'ongoing', 'won', 'lost'