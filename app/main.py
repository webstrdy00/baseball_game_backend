# app/main.py
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routers import game, auth, tetris
from .middleware.auth import auth_middleware
from dotenv import load_dotenv

load_dotenv()

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS 설정을 .env에서 가져오기
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["Authorization"],
    max_age=3600,  # preflight 요청 캐싱 시간(초)
)

# 미들웨어 등록
app.middleware("http")(auth_middleware)

# 라우터 등록
app.include_router(auth.router, tags=["auth"], prefix="/auth")
app.include_router(game.router, tags=["games"])
app.include_router(tetris.router, tags=["tetris"])