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
    is_admin: bool
    subscription_tier: SubscriptionTier
    subscription_expires_at: Optional[datetime]
    credits: int
    monthly_credits: int
    yearly_credits: int
    last_credit_refill: Optional[datetime]
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
    credits: int
    monthly_credits: int
    yearly_credits: int

# Credit schemas
class CreditPurchaseCreate(BaseModel):
    credits: int  # Number of credits to purchase

class CreditPurchaseResponse(BaseModel):
    id: int
    credits_purchased: int
    amount_paid: int
    currency: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

class CreditPack(BaseModel):
    id: str
    name: str
    credits: int
    price: int  # Price in cents
    price_display: str  # Formatted price like "$5.00"
    popular: bool = False

class UserCreditsResponse(BaseModel):
    credits: int
    monthly_credits: int
    yearly_credits: int
    last_credit_refill: Optional[datetime]

# Video processing schemas
class VideoUploadResponse(BaseModel):
    job_id: int
    message: str
    redirect_url: Optional[str] = None

class VideoDownloadResponse(BaseModel):
    download_url: str
    expires_at: datetime
