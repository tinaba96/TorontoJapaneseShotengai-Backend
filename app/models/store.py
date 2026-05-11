from typing import Optional
from pydantic import BaseModel, EmailStr, validator


class StoreBase(BaseModel):
    title: str
    description: str
    contactEmail: EmailStr
    contactPhone: Optional[str] = None
    businessHours: str
    website: Optional[str] = None
    services: Optional[str] = None
    storeAddress: str
    storeType: str

    @validator('storeType')
    def validate_store_type(cls, v):
        allowed = [
            'restaurant', 'cafe', 'grocery', 'bakery', 'clothing',
            'electronics', 'pharmacy', 'beauty', 'bank', 'convenience', 'other'
        ]
        if v not in allowed:
            raise ValueError(f'storeType must be one of: {allowed}')
        return v


class StoreCreate(StoreBase):
    pass


class Store(StoreBase):
    id: str
    creator_id: str
    status: str = "open"  # open, closed
    position_x: float
    position_y: float
    mainGenre: str
    subGenre: str
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True


class StoreUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    contactEmail: Optional[EmailStr] = None
    contactPhone: Optional[str] = None
    businessHours: Optional[str] = None
    website: Optional[str] = None
    services: Optional[str] = None
    storeAddress: Optional[str] = None
    storeType: Optional[str] = None
    status: Optional[str] = None
