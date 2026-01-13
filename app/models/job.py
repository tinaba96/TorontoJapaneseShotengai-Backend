from typing import Optional
from pydantic import BaseModel, EmailStr, validator

class JobBase(BaseModel):
    title: str
    description: str
    contactEmail: EmailStr
    contactPhone: Optional[str] = None
    company: str
    salary: str
    location: str
    jobType: str  # fulltime, parttime, contract, intern
    requirements: Optional[str] = None

    @validator('jobType')
    def validate_job_type(cls, v):
        allowed = ['fulltime', 'parttime', 'contract', 'intern']
        if v not in allowed:
            raise ValueError(f'jobType must be one of: {allowed}')
        return v

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
    jobType: Optional[str] = None
    requirements: Optional[str] = None
    status: Optional[str] = None

    @validator('jobType')
    def validate_job_type(cls, v):
        if v is None:
            return v
        allowed = ['fulltime', 'parttime', 'contract', 'intern']
        if v not in allowed:
            raise ValueError(f'jobType must be one of: {allowed}')
        return v