from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..core.security import create_access_token, get_current_user
from ..core.email import admin_emails
from ..crud.users import UserCRUD
from ..models.auth import Token
from pydantic import BaseModel
from typing import Optional

import os

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))  # Default to 30 if not set
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleLoginRequest(BaseModel):
    credential: str  # Google ID token (JWT) from the frontend


class MeResponse(BaseModel):
    id: str
    name: str
    email: str
    is_admin: bool


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """
    ユーザーログインエンドポイント
    """
    user = await UserCRUD.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# 既存のOAuth2形式のエンドポイント（FastAPIの標準的な認証に使用）
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await UserCRUD.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/google", response_model=Token)
async def google_login(data: GoogleLoginRequest):
    """
    Verify a Google ID token (sent from the frontend), upsert the user,
    and issue our own JWT access token — reusing the existing JWT infrastructure.
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google login is not configured (GOOGLE_CLIENT_ID missing).",
        )

    # Imported lazily so the rest of the app works even before google-auth is installed.
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server missing google-auth dependency.",
        )

    try:
        idinfo = google_id_token.verify_oauth2_token(
            data.credential, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential.",
        )

    email: Optional[str] = idinfo.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account has no email.",
        )
    name = idinfo.get("name") or email.split("@")[0]

    user = await UserCRUD.upsert_oauth_user(email=email, name=name)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=MeResponse)
async def read_me(current_user=Depends(get_current_user)):
    """Return the current user plus whether they are an admin (ADMIN_EMAILS)."""
    return MeResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        is_admin=current_user.email.lower() in admin_emails(),
    )
