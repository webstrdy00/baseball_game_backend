# app/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "숫자 야구 게임 백엔드 서버 입니다."}