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
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_expires_at = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    
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
