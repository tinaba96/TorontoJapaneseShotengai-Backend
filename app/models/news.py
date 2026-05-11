from typing import Optional, List
from pydantic import BaseModel


class NewsBase(BaseModel):
    title: str
    content: str  # body, can be HTML
    excerpt: Optional[str] = None
    category: str
    image: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    publishDate: Optional[str] = None  # ISO date (YYYY-MM-DD)


class NewsCreate(NewsBase):
    pass


class News(NewsBase):
    id: str
    creator_id: str
    status: str = "published"
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True


class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    category: Optional[str] = None
    image: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    publishDate: Optional[str] = None
    status: Optional[str] = None
