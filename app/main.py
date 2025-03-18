# app/main.py
import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import Base, engine, test_connection
from .routers import game, auth, tetris
from .middleware.auth import auth_middleware
from dotenv import load_dotenv
import time
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# 데이터베이스 연결 테스트
logger.info("애플리케이션 시작: 데이터베이스 연결 테스트 중...")
db_connected = test_connection()
if not db_connected:
    logger.warning("데이터베이스 연결에 실패했습니다. 일부 기능이 작동하지 않을 수 있습니다.")
else:
    logger.info("데이터베이스 연결이 정상적으로 확인되었습니다.")

try:
    # DB 테이블 생성
    logger.info("데이터베이스 테이블 생성 중...")
    Base.metadata.create_all(bind=engine)
    logger.info("데이터베이스 테이블 생성 완료")
except Exception as e:
    logger.error(f"데이터베이스 테이블 생성 실패: {str(e)}")

app = FastAPI(
    title="Baseball Score API",
    description="숫자 야구 게임과 테트리스 게임을 위한 API",
    version="1.0.0"
)

# CORS 설정을 .env에서 가져오기
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
logger.info(f"CORS 허용 도메인: {origins}")

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "Set-Cookie"],
    expose_headers=["Authorization", "Set-Cookie"],
    max_age=3600,  # preflight 요청 캐싱 시간(초)
)

# 미들웨어 등록
app.middleware("http")(auth_middleware)

# 라우터 등록
app.include_router(auth.router, tags=["auth"], prefix="/auth")
app.include_router(game.router, tags=["games"])
app.include_router(tetris.router, tags=["tetris"])

# 카카오 OAuth 설정 확인
if not os.getenv("KAKAO_CLIENT_ID"):
    logger.warning("KAKAO_CLIENT_ID가 설정되지 않았습니다. 카카오 로그인이 작동하지 않을 수 있습니다.")

# 미들웨어 설정
@app.middleware("http")
async def token_refresh_middleware(request: Request, call_next):
    """
    액세스 토큰이 만료된 경우 리프레시 토큰을 사용하여 자동으로 갱신하는 미들웨어
    """
    start_time = time.time()
    
    # 요청 처리
    response = await call_next(request)
    
    # 처리 시간 계산
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

@app.get("/")
def read_root():
    return {"message": "Baseball Score API에 오신 것을 환영합니다!"}

@app.get("/health")
def health_check():
    # 데이터베이스 연결 상태 확인
    db_status = "connected" if test_connection() else "disconnected"
    return {
        "status": "ok", 
        "message": "서버가 정상적으로 실행 중입니다.",
        "database": db_status,
        "environment": os.getenv("ENVIRONMENT", "development")
    }