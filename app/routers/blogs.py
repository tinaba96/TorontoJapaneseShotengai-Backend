from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models.blog import Blog, BlogCreate
from ..models import User
from ..crud.blogs import BlogCRUD
from app.core.security import get_current_user

router = APIRouter()


@router.get("/blogs/", response_model=List[Blog])
async def get_blogs():
    """
    Retrieve the list of all blog posts.
    """
    items = await BlogCRUD.get_all()
    if not items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No blogs found.")
    return items


@router.get("/blogs/{blog_id}", response_model=Blog)
async def get_blog_by_id(blog_id: str):
    """
    Retrieve a specific blog post by ID.
    """
    item = await BlogCRUD.get_by_id(blog_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found.")
    return item


@router.post("/blogs/", response_model=Blog, status_code=status.HTTP_201_CREATED)
async def create_blog(
    blog: BlogCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new blog post. Requires authentication.
    """
    try:
        return await BlogCRUD.create(blog, creator_id=current_user.id)
    except HTTPException as e:
        raise e
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create blog: {str(ex)}",
        )
