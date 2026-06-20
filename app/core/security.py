from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from app.core.utils import verify_password, get_password_hash, create_access_token  # utilsからインポート
import os

# OAuth2のスキーマを設定
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# 任意認証用（トークンが無くてもエラーにしない）
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

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


async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme_optional)):
    """
    トークンがあればユーザーを返し、無ければ None を返す（公開エンドポイントで、
    ログイン中なら追加情報を出したい場合に使う）。検証失敗時も None。
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None
    except JWTError:
        return None
    from app.crud.users import UserCRUD  # 遅延インポートで循環依存を回避

    return await UserCRUD.get_by_email(email)


async def get_admin_user(current_user=Depends(get_current_user)):
    """
    現在のユーザーが管理者（ADMIN_EMAILS に含まれる）かどうかを検証する。
    内見予約の管理画面など、運営者専用エンドポイントの保護に使う。
    """
    from app.core.email import admin_emails  # 遅延インポートで循環依存を回避

    if current_user.email.lower() not in admin_emails():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user