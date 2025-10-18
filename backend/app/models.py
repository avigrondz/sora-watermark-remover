from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

Base = declarative_base()

class SubscriptionTier(PyEnum):
    FREE = "free"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class JobStatus(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # Admin users have unlimited credits
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_expires_at = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    
    # Credit system
    credits = Column(Integer, default=0)  # Current available credits
    monthly_credits = Column(Integer, default=0)  # Credits allocated per month
    yearly_credits = Column(Integer, default=0)  # Credits allocated per year
    last_credit_refill = Column(DateTime, nullable=True)  # When credits were last refilled
    
    # Free trial tracking (commented out to avoid database migration issues)
    # free_uploads_used = Column(Integer, default=0)
    # free_uploads_limit = Column(Integer, default=1)  # 1 free upload
    # last_free_upload_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    jobs = relationship("Job", back_populates="user")

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    original_file_path = Column(String, nullable=False)
    processed_file_path = Column(String, nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    error_message = Column(Text, nullable=True)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    watermark_selections = Column(Text, nullable=True)  # JSON string of watermark selections
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="jobs")

class CreditPurchase(Base):
    __tablename__ = "credit_purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stripe_payment_intent_id = Column(String, nullable=True)  # For tracking Stripe payments
    credits_purchased = Column(Integer, nullable=False)
    amount_paid = Column(Integer, nullable=False)  # Amount in cents
    currency = Column(String, default="usd")
    status = Column(String, default="pending")  # pending, completed, failed
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")
