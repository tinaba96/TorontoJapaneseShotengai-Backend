from typing import Optional
from pydantic import BaseModel, EmailStr


class PropertyBase(BaseModel):
    title: str
    description: str
    contactEmail: EmailStr
    contactPhone: Optional[str] = None
    address: str
    rent: str
    size: str
    rooms: str
    utilities: Optional[str] = None
    parking: Optional[str] = None
    petPolicy: Optional[str] = None


class PropertyCreate(PropertyBase):
    pass


class Property(PropertyBase):
    id: str
    creator_id: str
    status: str = "available"  # available, rented
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True


class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    contactEmail: Optional[EmailStr] = None
    contactPhone: Optional[str] = None
    address: Optional[str] = None
    rent: Optional[str] = None
    size: Optional[str] = None
    rooms: Optional[str] = None
    utilities: Optional[str] = None
    parking: Optional[str] = None
    petPolicy: Optional[str] = None
    status: Optional[str] = None
