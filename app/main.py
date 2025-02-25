# app/main.py
from fastapi import FastAPI, Request
from .database import Base, engine
from .routers import game, auth
from .middleware.auth import auth_middleware

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 미들웨어 등록
app.middleware("http")(auth_middleware)

# 라우터 등록
app.include_router(auth.router, tags=["auth"], prefix="/auth")
app.include_router(game.router, tags=["games"])