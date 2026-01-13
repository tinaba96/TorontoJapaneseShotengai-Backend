from typing import Optional, Literal
from pydantic import BaseModel, EmailStr

JobType = Literal["fulltime", "parttime", "contract", "intern"]

class JobBase(BaseModel):
    title: str
    description: str
    contactEmail: EmailStr
    contactPhone: Optional[str] = None
    company: str
    salary: str
    location: str
    jobType: JobType
    requirements: Optional[str] = None

class JobCreate(JobBase):
    pass

class Job(JobBase):
    id: str
    creator_id: str
    status: str = "open"  # open, closed
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    contactEmail: Optional[EmailStr] = None
    contactPhone: Optional[str] = None
    company: Optional[str] = None
    salary: Optional[str] = None
    location: Optional[str] = None
    jobType: Optional[JobType] = None
    requirements: Optional[str] = None
    status: Optional[str] = None