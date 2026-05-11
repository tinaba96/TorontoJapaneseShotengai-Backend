from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models.product import Product, ProductCreate
from ..models import User
from ..crud.products import ProductCRUD
from app.core.security import get_current_user

router = APIRouter()


@router.get("/products/", response_model=List[Product])
async def get_products():
    """
    Retrieve the list of all products.
    """
    products = await ProductCRUD.get_all()
    if not products:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No products found.")
    return products


@router.post("/products/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new product. Requires authentication.
    The authenticated user will be set as the product creator.
    """
    try:
        return await ProductCRUD.create(product, creator_id=current_user.id)
    except HTTPException as e:
        raise e
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(ex)}",
        )
