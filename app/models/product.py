from typing import Optional
from pydantic import BaseModel, EmailStr, validator


class ProductBase(BaseModel):
    title: str
    description: str
    contactEmail: EmailStr
    contactPhone: Optional[str] = None
    price: str
    condition: str  # new, like-new, good, fair, poor
    category: str  # electronics, clothing, furniture, books, sports, other
    images: Optional[str] = None

    @validator('condition')
    def validate_condition(cls, v):
        allowed = ['new', 'like-new', 'good', 'fair', 'poor']
        if v not in allowed:
            raise ValueError(f'condition must be one of: {allowed}')
        return v

    @validator('category')
    def validate_category(cls, v):
        allowed = ['electronics', 'clothing', 'furniture', 'books', 'sports', 'other']
        if v not in allowed:
            raise ValueError(f'category must be one of: {allowed}')
        return v


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: str
    creator_id: str
    status: str = "available"  # available, sold
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    contactEmail: Optional[EmailStr] = None
    contactPhone: Optional[str] = None
    price: Optional[str] = None
    condition: Optional[str] = None
    category: Optional[str] = None
    images: Optional[str] = None
    status: Optional[str] = None
