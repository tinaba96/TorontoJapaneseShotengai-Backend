from fastapi import APIRouter, Depends
from typing import List
from ..models import User, UserCreate, UserUpdate
from ..crud.users import UserCRUD
from ..core.security import get_current_user

router = APIRouter()


@router.post("/users/", response_model=User)
async def create_user(user: UserCreate):
    return await UserCRUD.create(user)


@router.get("/users/", response_model=List[User])
async def get_users():
    return await UserCRUD.get_all()


@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    return await UserCRUD.get_by_id(user_id)


@router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user: UserUpdate):
    return await UserCRUD.update(user_id, user)


@router.delete("/users/{user_id}")
async def delete_user(user_id: int):
    return await UserCRUD.delete(user_id)


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    現在ログインしているユーザーの情報を取得するエンドポイント
    """
    return current_user
