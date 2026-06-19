from typing import Optional
from pydantic import BaseModel, EmailStr


# ----- Availability windows (admin が登録する「可能な期間」) -----
class AvailabilityWindowCreate(BaseModel):
    starts_at: str  # ISO 8601 (UTC推奨)
    ends_at: str    # ISO 8601 (UTC推奨)


class AvailabilityWindow(AvailabilityWindowCreate):
    id: str
    created_at: str

    class Config:
        orm_mode = True


# ----- Derived 30-min slots (公開・期間から自動生成) -----
class AvailabilitySlot(BaseModel):
    starts_at: str          # 30分枠の開始（ISO 8601, UTC）
    booking_count: int = 0


# ----- Bookings -----
class ViewingBookingCreate(BaseModel):
    starts_at: str          # 選択した30分枠の開始（ISO 8601）
    name: str
    email: EmailStr
    phone: Optional[str] = None


class ViewingBooking(BaseModel):
    id: str
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
