from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models.news import News, NewsCreate
from ..models import User
from ..crud.news import NewsCRUD
from app.core.security import get_current_user

router = APIRouter()


@router.get("/news/", response_model=List[News])
async def get_news():
    """
    Retrieve the list of all news.
    """
    items = await NewsCRUD.get_all()
    if not items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No news found.")
    return items


@router.get("/news/{news_id}", response_model=News)
async def get_news_by_id(news_id: str):
    """
    Retrieve a specific news article by ID.
    """
    item = await NewsCRUD.get_by_id(news_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found.")
    return item


@router.post("/news/", response_model=News, status_code=status.HTTP_201_CREATED)
async def create_news(
    news: NewsCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new news article. Requires authentication.
    """
    try:
        return await NewsCRUD.create(news, creator_id=current_user.id)
    except HTTPException as e:
        raise e
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create news: {str(ex)}",
        )
