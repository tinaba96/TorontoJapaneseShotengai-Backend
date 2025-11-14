from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from typing import Union
import os

# パスワードのハッシュ化関連
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    平文のパスワードがハッシュ化されたパスワードと一致するか検証
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    パスワードをハッシュ化
    """
    return pwd_context.hash(password)

# JWTトークン関連
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")  # 環境変数から読み込み
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """
    JWTアクセストークンを作成
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt