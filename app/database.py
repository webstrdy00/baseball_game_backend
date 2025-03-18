# app/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .env 파일 다시 로드 (적용 확인)
load_dotenv(override=True)

# 데이터베이스 URL 직접 설정 - .env 파일에서 가져오기
DATABASE_URL = os.getenv("DATABASE_URL")

# 데이터베이스 URL이 비어있는 경우 기본값 설정
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:12345@localhost:5432/baseball_game"
    logger.warning("DATABASE_URL이 설정되지 않아 기본 로컬 데이터베이스를 사용합니다.")

# 데이터베이스 연결 정보 로깅 (비밀번호 제외)
try:
    db_parts = DATABASE_URL.split("@")
    if len(db_parts) > 1:
        db_info = db_parts[1]
        logger.info(f"데이터베이스 연결 정보 (호스트:포트): {db_info}")
    else:
        logger.warning("데이터베이스 연결 문자열 형식이 올바르지 않습니다.")
except Exception as e:
    logger.error(f"데이터베이스 연결 정보 파싱 오류: {str(e)}")

try:
    # SQLAlchemy 1.4 이상 버전에 맞는 옵션 추가
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # SQL 쿼리 로깅 비활성화
        pool_pre_ping=True,  # 연결 확인
        connect_args={
            # 필요한 경우 추가 연결 옵션 설정
            # "sslmode": "require"  # SSL 필요 (Supabase)
        }
    )
    logger.info("데이터베이스 엔진 생성 성공")
except Exception as e:
    logger.error(f"데이터베이스 엔진 생성 실패: {str(e)}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블 생성 완료")
    except Exception as e:
        logger.error(f"데이터베이스 테이블 생성 실패: {str(e)}")
        raise
    
def get_db():
    db = SessionLocal()
    try:
        logger.debug("데이터베이스 세션 생성")
        yield db
    finally:
        db.close()
        logger.debug("데이터베이스 세션 종료")

# 애플리케이션 시작시 데이터베이스 테이블 생성 가능 여부 테스트
def test_connection():
    try:
        # 간단한 쿼리 실행 - text() 함수 사용
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            # 결과 확인
            for row in result:
                logger.info(f"테스트 쿼리 결과: {row}")
            logger.info("데이터베이스 연결 테스트 성공!")
            return True
    except Exception as e:
        logger.error(f"데이터베이스 연결 테스트 실패: {str(e)}")
        return False