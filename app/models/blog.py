from typing import Optional
from pydantic import BaseModel


class BlogBase(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    category: str  # e.g. BEAUTY, EXPERIENCE
    image: Optional[str] = None
    publishDate: Optional[str] = None  # ISO date (YYYY-MM-DD)


class BlogCreate(BlogBase):
    pass


class Blog(BlogBase):
    id: str
    creator_id: str
    status: str = "published"
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True


class BlogUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    category: Optional[str] = None
    image: Optional[str] = None
    publishDate: Optional[str] = None
    status: Optional[str] = None
