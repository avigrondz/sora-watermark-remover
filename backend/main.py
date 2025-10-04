from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import tempfile
from datetime import datetime, timedelta

from app.database import get_db, engine
from app.models import Base, User, Job, JobStatus, SubscriptionTier
from app.schemas import (
    UserCreate, UserLogin, User as UserSchema, Token,
    JobCreate, Job as JobSchema, JobStatusResponse,
    VideoUploadResponse, VideoDownloadResponse,
    SubscriptionCreate, SubscriptionResponse
)
from app.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_active_user, verify_token
)
from app.tasks import process_video
from services.s3_service import s3_service

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sora Watermark Remover API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
<<<<<<< HEAD
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001",
        "https://front-end-production-1f77.up.railway.app"
    ],  # Frontend URLs
=======
    allow_origins=["*"],  # Allow all origins temporarily
>>>>>>> f8582f4cdadbe28d6b5b906f010cfcce49c09a83
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# User registration
@app.post("/api/auth/register", response_model=UserSchema)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        subscription_tier=SubscriptionTier.FREE
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

# User login
@app.post("/api/auth/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    # Authenticate user
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# Get current user
@app.get("/api/auth/me", response_model=UserSchema)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Upload video for processing
@app.post("/api/videos/upload", response_model=VideoUploadResponse)
def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check subscription status
    if current_user.subscription_tier == SubscriptionTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription required for video processing"
        )
    
    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a video"
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        content = file.file.read()
        temp_file.write(content)
        temp_path = temp_file.name
    
    # Upload to S3
    s3_key = f"uploads/{current_user.id}/{unique_filename}"
    if not s3_service.upload_file(temp_path, s3_key):
        os.unlink(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )
    
    # Create job record
    job = Job(
        user_id=current_user.id,
        original_filename=file.filename,
        original_file_path=s3_key,
        status=JobStatus.PENDING
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Start processing task
    process_video.delay(job.id)
    
    # Clean up temp file
    os.unlink(temp_path)
    
    return VideoUploadResponse(
        job_id=job.id,
        message="Video uploaded successfully. Processing started."
    )

# Get job status
@app.get("/api/jobs/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        error_message=job.error_message
    )

# Get user's jobs
@app.get("/api/jobs", response_model=List[JobSchema])
def get_user_jobs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    jobs = db.query(Job).filter(Job.user_id == current_user.id).order_by(Job.created_at.desc()).all()
    return jobs

# Download processed video
@app.get("/api/jobs/{job_id}/download", response_model=VideoDownloadResponse)
def download_video(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job not completed yet"
        )
    
    if not job.processed_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processed file not found"
        )
    
    # Generate presigned URL for download
    download_url = s3_service.generate_presigned_url(
        job.processed_file_path,
        expiration=3600  # 1 hour
    )
    
    if not download_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download link"
        )
    
    return VideoDownloadResponse(
        download_url=download_url,
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )

# Health check
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
