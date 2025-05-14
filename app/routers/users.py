from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models import User, UserCreate, UserUpdate
from ..crud.users import UserCRUD
from app.core.security import get_current_user

router = APIRouter()


@router.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """
    Create a new user in the system.
    """
    try:
        return await UserCRUD.create(user)
    except HTTPException as e:
        # 再スロー（詳細メッセージをそのまま利用するため）
        raise e
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(ex)}",
        )


@router.get("/users/", response_model=List[User])
async def get_users():
    """
    Retrieve the list of all users.
    """
    users = await UserCRUD.get_all()
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found.")
    return users


@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """
    Retrieve a specific user by ID.
    """
    user = await UserCRUD.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


@router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user: UserUpdate):
    """
    Update user details by user ID.
    """
    updated_user = await UserCRUD.update(user_id, user)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return updated_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    """
    Delete a user by ID.
    """
    success = await UserCRUD.delete(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get the details of the currently authenticated user.
    """
    return current_user