from typing import Optional
from pydantic import BaseModel, EmailStr


class ViewingSlotCreate(BaseModel):
    # ISO 8601 datetime string (UTC recommended). Start of a 30-minute slot.
    starts_at: str


class ViewingSlot(ViewingSlotCreate):
    id: str
    booking_count: int = 0
    created_at: str

    class Config:
        orm_mode = True


class ViewingBookingCreate(BaseModel):
    slot_id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None


class ViewingBooking(BaseModel):
    id: str
    slot_id: str
    starts_at: Optional[str] = None
    name: str
    email: EmailStr
    phone: Optional[str] = None
    status: str = "active"  # active | cancelled
    created_at: str

    class Config:
        orm_mode = True


class CancelRequest(BaseModel):
    token: str
