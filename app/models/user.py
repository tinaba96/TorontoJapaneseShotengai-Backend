from typing import Optional
from pydantic import BaseModel

class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password: str
    id: Optional[str] = None  # `id`を任意のフィールドとして設定

class User(UserBase):
    id: str  # データベースから返却される際には必須
    created_at: str

    class Config:
        orm_mode = True
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
