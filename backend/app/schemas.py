from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models import SubscriptionTier, JobStatus

# User schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    is_active: bool
    subscription_tier: SubscriptionTier
    subscription_expires_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Job schemas
class JobBase(BaseModel):
    original_filename: str

class JobCreate(JobBase):
    pass

class Job(JobBase):
    id: int
    user_id: int
    original_file_path: str
    processed_file_path: Optional[str]
    status: JobStatus
    error_message: Optional[str]
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class JobStatusResponse(BaseModel):
    job_id: int
    status: JobStatus
    progress: Optional[float] = None
    error_message: Optional[str] = None

# Subscription schemas
class SubscriptionCreate(BaseModel):
    price_id: str  # Stripe price ID

class SubscriptionResponse(BaseModel):
    subscription_tier: SubscriptionTier
    expires_at: Optional[datetime]

# Video processing schemas
class VideoUploadResponse(BaseModel):
    job_id: int
    message: str

class VideoDownloadResponse(BaseModel):
    download_url: str
    expires_at: datetime
