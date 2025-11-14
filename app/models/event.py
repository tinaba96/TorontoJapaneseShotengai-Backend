from typing import Optional
from pydantic import BaseModel, EmailStr

class EventBase(BaseModel):
    title: str
    description: str
    contactEmail: EmailStr
    contactPhone: Optional[str] = None
    eventDate: str  # YYYY-MM-DD format
    eventTime: str  # HH:MM format
    venue: str
    organizer: str
    maxAttendees: Optional[int] = None

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: str
    creator_id: str  # User who created the event
    current_attendees: int = 0
    status: str = "upcoming"  # upcoming, ongoing, completed, cancelled
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    contactEmail: Optional[EmailStr] = None
    contactPhone: Optional[str] = None
    eventDate: Optional[str] = None
    eventTime: Optional[str] = None
    venue: Optional[str] = None
    organizer: Optional[str] = None
    maxAttendees: Optional[int] = None
    status: Optional[str] = None