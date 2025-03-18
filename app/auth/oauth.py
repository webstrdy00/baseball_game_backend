import httpx
import json
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, UTC
import os
from typing import Dict, Any, Optional

from .. import models, schemas, crud
from ..database import get_db
from ..auth.utils import create_access_token, create_refresh_token

# 카카오 OAuth 설정
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID", "")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", "")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "")

# 카카오 API 엔드포인트
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"

async def get_kakao_token(code: str) -> Dict[str, Any]:
    """
    카카오 인증 코드를 사용하여 액세스 토큰을 얻습니다.
    
    Args:
        code: 카카오 인증 코드
    
    Returns:
        토큰 정보를 담은 딕셔너리
    """
    if not KAKAO_CLIENT_ID or not KAKAO_REDIRECT_URI:
        raise HTTPException(
            status_code=500,
            detail="카카오 OAuth 설정이 완료되지 않았습니다."
        )
    
    data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code
    }
    
    if KAKAO_CLIENT_SECRET:
        data["client_secret"] = KAKAO_CLIENT_SECRET
    
    async with httpx.AsyncClient() as client:
        response = await client.post(KAKAO_TOKEN_URL, data=data)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"카카오 토큰 요청 실패: {response.text}"
            )
        
        return response.json()

async def get_kakao_user_info(access_token: str) -> Dict[str, Any]:
    """
    카카오 액세스 토큰을 사용하여 사용자 정보를 얻습니다.
    
    Args:
        access_token: 카카오 액세스 토큰
    
    Returns:
        사용자 정보를 담은 딕셔너리
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(KAKAO_USER_INFO_URL, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"카카오 사용자 정보 요청 실패: {response.text}"
            )
        
        return response.json()

async def process_kakao_login(code: str, db: Session) -> schemas.LoginResponse:
    """
    카카오 로그인 처리를 수행합니다.
    
    Args:
        code: 카카오 인증 코드
        db: 데이터베이스 세션
    
    Returns:
        로그인 응답 객체
    """
    # 카카오 토큰 얻기
    token_info = await get_kakao_token(code)
    kakao_access_token = token_info.get("access_token")
    
    if not kakao_access_token:
        raise HTTPException(
            status_code=400,
            detail="카카오 액세스 토큰을 얻을 수 없습니다."
        )
    
    # 카카오 사용자 정보 얻기
    user_info = await get_kakao_user_info(kakao_access_token)
    
    # 필요한 정보 추출
    kakao_id = str(user_info.get("id"))
    kakao_account = user_info.get("kakao_account", {})
    profile = kakao_account.get("profile", {})
    
    email = kakao_account.get("email")
    nickname = profile.get("nickname")
    
    if not email:
        # 이메일이 없는 경우 카카오 ID를 사용하여 가상 이메일 생성
        email = f"kakao_{kakao_id}@example.com"
    
    if not nickname:
        # 닉네임이 없는 경우 기본값 설정
        nickname = f"User_{kakao_id}"
    
    # 이미 가입된 사용자인지 확인
    user = crud.get_user_by_social_id(db, social_id=kakao_id, social_type="kakao")
    
    if not user:
        # 이메일로 사용자 확인 (이미 일반 계정으로 가입한 경우)
        existing_user = crud.get_user_by_email(db, email=email)
        
        if existing_user:
            # 기존 계정에 소셜 정보 연결
            existing_user.social_id = kakao_id
            existing_user.social_type = "kakao"
            db.commit()
            db.refresh(existing_user)
            user = existing_user
        else:
            # 새 사용자 생성
            social_user = schemas.SocialUserCreate(
                email=email,
                username=nickname,
                social_id=kakao_id,
                social_type="kakao"
            )
            user = crud.create_social_user(db, user=social_user)
    
    # JWT 토큰 생성
    access_token = create_access_token(data={"sub": user.email, "id": user.id})
    refresh_token = create_refresh_token(data={"sub": user.email, "id": user.id})
    
    return schemas.LoginResponse(
        user=schemas.UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at
        ),
        access_token=access_token,
        refresh_token=refresh_token
    ) 