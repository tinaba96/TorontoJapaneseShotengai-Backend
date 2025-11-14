from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from app.core.utils import verify_password, get_password_hash, create_access_token  # utilsからインポート
import os

# OAuth2のスキーマを設定
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT設定
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")  # 環境変数から読み込み
ALGORITHM = "HS256"

async def decode_token(token: str = Depends(oauth2_scheme)) -> str:
    """
    トークンをデコードしてemailを抽出
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return email
    except JWTError:
        raise credentials_exception

async def get_current_user(email: str = Depends(decode_token)):
    """
    トークンから取得したemailを利用して、現在のユーザーを取得
    """
    from app.crud.users import UserCRUD  # 遅延インポートで循環依存を回避

    user = await UserCRUD.get_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user