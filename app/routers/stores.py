from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models.store import Store, StoreCreate
from ..models import User
from ..crud.stores import StoreCRUD
from app.core.security import get_current_user

router = APIRouter()


@router.get("/stores/", response_model=List[Store])
async def get_stores():
    """
    Retrieve the list of all stores.
    """
    stores = await StoreCRUD.get_all()
    if not stores:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No stores found.")
    return stores


@router.post("/stores/", response_model=Store, status_code=status.HTTP_201_CREATED)
async def create_store(
    store: StoreCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new store posting. Requires authentication.
    The authenticated user will be set as the store creator.
    """
    try:
        return await StoreCRUD.create(store, creator_id=current_user.id)
    except HTTPException as e:
        raise e
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create store: {str(ex)}",
        )
