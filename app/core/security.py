from datetime import datetime, timedelta
from typing import Optional, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# パスワードハッシュのコンテキスト設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2のスキーマを設定
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT設定
SECRET_KEY = "your-secret-key"  # 本番環境では環境変数から取得すべき
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def decode_token(token: str = Depends(oauth2_scheme)) -> str:
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
from typing import Optional, List
from fastapi import HTTPException
from ..models import User, UserCreate, UserUpdate
from . import db
from ..core.security import verify_password, get_password_hash
from fastapi import APIRouter, Depends
from typing import List
from ..models import User, UserCreate, UserUpdate
from ..crud.users import UserCRUD
from ..core.security import decode_token

router = APIRouter()

async def get_current_user(email: str = Depends(decode_token)) -> User:
    user = await UserCRUD.get_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# ... 他のエンドポイントはそのまま ...
class UserCRUD:
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[User]:
        with db.get_session() as session:
            result = session.run("MATCH (u:User {email: $email}) RETURN u", email=email)
            record = result.single()
            if not record:
                return None
            user_data = record["u"]
            if not verify_password(password, user_data["hashed_password"]):
                return None
            return User(
                id=user_data.id,
                name=user_data["name"],
                email=user_data["email"],
                created_at=user_data["created_at"].isoformat(),
            )

    # ... 他のメソッドはそのまま ...