# app/main.py
from fastapi import FastAPI
from .database import Base, engine
from .routers import game

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 라우터 등록
app.include_router(game.router, tags=["games"])