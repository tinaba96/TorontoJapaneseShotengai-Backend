from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models.property import Property, PropertyCreate
from ..models import User
from ..crud.properties import PropertyCRUD
from app.core.security import get_current_user

router = APIRouter()


@router.get("/properties/", response_model=List[Property])
async def get_properties():
    """
    Retrieve the list of all properties.
    """
    properties = await PropertyCRUD.get_all()
    if not properties:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No properties found.")
    return properties


@router.post("/properties/", response_model=Property, status_code=status.HTTP_201_CREATED)
async def create_property(
    prop: PropertyCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new property posting. Requires authentication.
    The authenticated user will be set as the property creator.
    """
    try:
        return await PropertyCRUD.create(prop, creator_id=current_user.id)
    except HTTPException as e:
        raise e
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create property: {str(ex)}",
        )
