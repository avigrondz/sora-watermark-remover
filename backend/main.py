from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import RedirectResponse, FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import os
import subprocess
import uuid
import tempfile
import stripe
from datetime import datetime, timedelta
import json

from app.database import get_db, engine
from app.models import Base, User, Job, JobStatus, SubscriptionTier, CreditPurchase
from app.schemas import (
    UserCreate, UserLogin, User as UserSchema, Token,
    JobCreate, Job as JobSchema, JobStatusResponse,
    VideoUploadResponse, VideoDownloadResponse,
    SubscriptionCreate, SubscriptionResponse,
    CreditPurchaseCreate, CreditPurchaseResponse, CreditPack, UserCreditsResponse
)
from app.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_active_user, verify_token
)
from app.tasks import process_video
from services.s3_service import s3_service
from services.local_storage import local_storage
from services.video_processor import process_video_with_delogo

# Create database tables
Base.metadata.create_all(bind=engine)

# Run database migrations
def run_startup_migrations():
    """Run any necessary database migrations on startup"""
    try:
        from sqlalchemy import text
        from app.database import engine
        
        with engine.connect() as connection:
            # Check if watermark_selections column exists
            check_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'jobs' AND column_name = 'watermark_selections';
            """
            
            result = connection.execute(text(check_sql))
            existing_columns = [row[0] for row in result]
            
            if 'watermark_selections' not in existing_columns:
                print("🔄 Adding watermark_selections column...")
                migration_sql = "ALTER TABLE jobs ADD COLUMN watermark_selections TEXT;"
                connection.execute(text(migration_sql))
                connection.commit()
                print("✅ Added watermark_selections column")
            else:
                print("✅ watermark_selections column already exists")
                
    except Exception as e:
        error_msg = str(e).lower()
        if "duplicate column name" in error_msg or "column already exists" in error_msg:
            print("✅ watermark_selections column already exists")
        else:
            print(f"⚠️ Migration warning: {e}")

# Run migrations on startup
run_startup_migrations()

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Stripe price IDs (you'll need to create these in your Stripe dashboard)
STRIPE_PRICE_IDS = {
    "monthly": os.getenv("STRIPE_MONTHLY_PRICE_ID", "price_monthly_placeholder"),
    "yearly": os.getenv("STRIPE_YEARLY_PRICE_ID", "price_yearly_placeholder"),
    # Credit pack price IDs
    "credits_10": os.getenv("STRIPE_CREDITS_10_PRICE_ID", "price_credits_10_placeholder"),
    "credits_25": os.getenv("STRIPE_CREDITS_25_PRICE_ID", "price_credits_25_placeholder"),
    "credits_50": os.getenv("STRIPE_CREDITS_50_PRICE_ID", "price_credits_50_placeholder"),
    "credits_100": os.getenv("STRIPE_CREDITS_100_PRICE_ID", "price_credits_100_placeholder"),
}

# Credit system configuration
CREDIT_PACKS = [
    {"id": "credits_10", "name": "10 Credits", "credits": 10, "price": 500, "price_display": "$5.00", "popular": False},
    {"id": "credits_25", "name": "25 Credits", "credits": 25, "price": 1000, "price_display": "$10.00", "popular": True},
    {"id": "credits_50", "name": "50 Credits", "credits": 50, "price": 1800, "price_display": "$18.00", "popular": False},
    {"id": "credits_100", "name": "100 Credits", "credits": 100, "price": 3000, "price_display": "$30.00", "popular": False},
]

# Subscription credit allocations
SUBSCRIPTION_CREDITS = {
    "monthly": 20,  # 20 credits per month for $12
    "yearly": 300,  # 300 credits per year for $70 (better value)
}

app = FastAPI(title="Sora Watermark Remover API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
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

# Handle CORS preflight requests for public upload
@app.options("/api/public/upload")
def public_upload_options():
    """Handle CORS preflight requests for public upload"""
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        }
    )

# Public upload endpoint for embed widget (no authentication required)
@app.post("/api/public/upload", response_model=VideoUploadResponse)
def public_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Public upload endpoint for embed widget - no authentication required"""
    # Ensure a placeholder public user exists to satisfy NOT NULL jobs.user_id
    public_user = db.query(User).filter(User.email == "public@sora.local").first()
    if not public_user:
        try:
            public_user = User(
                email="public@sora.local",
                hashed_password=get_password_hash(str(uuid.uuid4())),
                subscription_tier=SubscriptionTier.FREE,
            )
            db.add(public_user)
            db.commit()
            db.refresh(public_user)
            print(f"✅ Created public user: {public_user.id}")
        except Exception as e:
            print(f"❌ Failed to create public user: {e}")
            db.rollback()
            # Try to get existing user after rollback
            public_user = db.query(User).filter(User.email == "public@sora.local").first()
            if not public_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create public user for anonymous uploads"
                )
    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a video"
        )
    
    # Validate file size (500MB limit)
    file_size = 0
    content = file.file.read()
    file_size = len(content)
    file.file.seek(0)  # Reset file pointer
    
    max_size = 500 * 1024 * 1024  # 500MB
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 500MB"
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name
    
    # Upload to local storage (public uploads go to free tier)
    s3_key = f"uploads/free/public/{unique_filename}"
    
    # Use S3 only if explicitly enabled (disabled by default for localhost)
    use_s3 = os.getenv("USE_S3", "false").lower() == "true"
    upload_success = False
    
    if use_s3:
        try:
            upload_success = s3_service.upload_file(temp_path, s3_key)
            print(f"✅ File uploaded to S3: {s3_key}")
        except Exception as e:
            print(f"⚠️ S3 upload failed, using local storage: {e}")
            upload_success = local_storage.upload_file(temp_path, s3_key)
    else:
        print(f"📁 Storing file locally (S3 disabled): {s3_key}")
        upload_success = local_storage.upload_file(temp_path, s3_key)
    
    if not upload_success:
        os.unlink(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )
    
    # Create job record (attach to public user)
    job = Job(
        user_id=public_user.id,
        original_filename=file.filename,
        original_file_path=s3_key,
        status=JobStatus.PENDING
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Return response with redirect URL
    print(f"✅ Public job {job.id} created successfully")
    
    # Clean up temp file
    try:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            print(f"✅ Temp file cleaned up: {temp_path}")
    except Exception as e:
        print(f"⚠️  Temp file cleanup failed: {e}")
    
    return VideoUploadResponse(
        job_id=job.id,
        message="Video uploaded successfully. Proceed to select watermarks.",
        redirect_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/process/{job.id}"
    )

# Handle CORS preflight for public job status
@app.options("/api/public/jobs/{job_id}/status")
def public_job_status_options():
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        }
    )

# Public: get job status (no auth)
@app.get("/api/public/jobs/{job_id}/status")
def public_get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.id,
        "status": job.status,
        "has_processed": bool(job.processed_file_path),
    }

# Public: save watermark selections
@app.post("/api/public/jobs/{job_id}/watermarks")
def public_add_watermarks(job_id: int, watermark_data: dict, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
        raise HTTPException(status_code=400, detail="Job not in editable state")
    job.watermark_selections = json.dumps(watermark_data)
    db.commit()
    return {"message": "Watermark selection saved", "job_id": job_id}

# Public: start processing
@app.post("/api/public/jobs/{job_id}/process")
def public_start_processing(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.PENDING:
        raise HTTPException(status_code=400, detail="Job is not in pending state")
    job.status = JobStatus.PROCESSING
    job.processing_started_at = datetime.utcnow()
    db.commit()

    import threading
    def process_video_async():
        from app.database import SessionLocal
        background_db = SessionLocal()
        try:
            bg_job = background_db.query(Job).filter(Job.id == job.id).first()
            if not bg_job:
                return
            try:
                out_path = process_video_with_delogo(
                    original_file_path=bg_job.original_file_path,
                    processed_file_path=bg_job.processed_file_path,
                    watermark_selections_json=bg_job.watermark_selections,
                    user_id=bg_job.user_id or 0,
                )
                bg_job.status = JobStatus.COMPLETED
                bg_job.processed_file_path = out_path
                bg_job.processing_completed_at = datetime.utcnow()
                background_db.commit()
                print(f"✅ Public job {bg_job.id} processing completed: {out_path}")
            except Exception as e:
                bg_job.status = JobStatus.FAILED
                bg_job.error_message = str(e)
                background_db.commit()
                print(f"❌ Public job {bg_job.id} processing failed: {e}")
        finally:
            background_db.close()

    thread = threading.Thread(target=process_video_async)
    thread.start()
    return {"message": "Processing started", "job_id": job_id}

# Upload video for processing (authenticated users)
@app.post("/api/videos/upload", response_model=VideoUploadResponse)
def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check credits for processing (admin users have unlimited access)
    if current_user.is_admin:
        # Admin users have unlimited access
        print(f"✅ Admin user {current_user.email} - unlimited access granted")
    elif current_user.subscription_tier == SubscriptionTier.FREE:
        # Free users get 1 free upload
        existing_jobs = db.query(Job).filter(Job.user_id == current_user.id).count()
        if existing_jobs >= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free trial limit reached. Please subscribe or purchase credits to continue."
            )
    else:
        # Paid users need credits
        if current_user.credits <= 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient credits. Please purchase more credits to continue."
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
    
    # Upload to S3 with organized path structure
    if current_user.subscription_tier == SubscriptionTier.FREE:
        s3_key = f"uploads/free/{current_user.id}/{unique_filename}"
    else:
        s3_key = f"uploads/paid/{current_user.id}/{unique_filename}"
    
    # Try S3 first, fallback to local storage
    upload_success = False
    try:
        upload_success = s3_service.upload_file(temp_path, s3_key)
    except Exception as e:
        print(f"S3 upload failed, using local storage: {e}")
        upload_success = local_storage.upload_file(temp_path, s3_key)
    
    if not upload_success:
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
    
    # Deduct credit for paid users (skip admin users)
    if not current_user.is_admin and current_user.subscription_tier != SubscriptionTier.FREE:
        current_user.credits -= 1
        print(f"✅ Deducted 1 credit from user {current_user.id}. Remaining credits: {current_user.credits}")
    elif current_user.is_admin:
        print(f"✅ Admin user {current_user.email} - no credit deduction")
    
    db.commit()
    db.refresh(job)
    
    # Return response immediately; keep job in PENDING so user can select watermarks
    print(f"✅ Job {job.id} created successfully (awaiting watermark selections)")
    
    # Clean up temp file
    try:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            print(f"✅ Temp file cleaned up: {temp_path}")
    except Exception as e:
        print(f"⚠️  Temp file cleanup failed: {e}")
    
    return VideoUploadResponse(
        job_id=job.id,
        message="Video uploaded successfully. Proceed to select watermarks."
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
    
    # Generate download URL - always use local server for development
    download_url = None
    
    # Prefer S3 first when key looks like an S3 key
    try:
        if job.processed_file_path.startswith("uploads/"):
            download_url = s3_service.generate_presigned_url(
                job.processed_file_path,
                expiration=3600
            )
            if download_url:
                print(f"✅ Generated S3 download URL for processed file: {job.processed_file_path}")
    except Exception as e:
        print(f"⚠️ S3 presign failed, will try local: {e}")

    # If S3 wasn't available, fall back to local streaming endpoint
    if not download_url:
        actual_file_path = None
        # Direct path stored
        if job.processed_file_path and os.path.isabs(job.processed_file_path) and os.path.exists(job.processed_file_path):
            actual_file_path = job.processed_file_path
            print(f"✅ Using absolute processed path: {actual_file_path}")
        else:
            # Try to find in local storage by filename match
            print(f"Searching for processed file locally: {job.processed_file_path}")
            for root, dirs, files in os.walk("local_storage"):
                for name in files:
                    if name in job.processed_file_path:
                        candidate = os.path.join(root, name)
                        if os.path.exists(candidate):
                            actual_file_path = candidate
                            print(f"✅ Found processed file in local storage: {candidate}")
                            break
                if actual_file_path:
                    break

        if actual_file_path and os.path.exists(actual_file_path):
            download_url = f"http://localhost:8000/api/videos/{job.id}/stream"
            print(f"✅ Using local streaming URL for download: {download_url}")
    
    if not download_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download link"
        )
    
    return VideoDownloadResponse(
        download_url=download_url,
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )

# Delete job
@app.delete("/api/jobs/{job_id}")
def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a job and its associated files"""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    try:
        # Delete files from storage
        files_to_delete = []
        if job.original_file_path:
            files_to_delete.append(job.original_file_path)
        if job.processed_file_path:
            files_to_delete.append(job.processed_file_path)
        
        for file_path in files_to_delete:
            try:
                if file_path.startswith("uploads/"):
                    # Try S3 first
                    s3_service.delete_file(file_path)
                else:
                    # Local file
                    if os.path.exists(file_path):
                        os.unlink(file_path)
            except Exception as e:
                print(f"Warning: Could not delete file {file_path}: {e}")
        
        # Delete job from database
        db.delete(job)
        db.commit()
        
        return {"message": "Job deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}"
        )

# Health check
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Watermark selection endpoints
@app.post("/api/jobs/{job_id}/watermarks")
def add_watermark_selection(
    job_id: int,
    watermark_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add watermark selection to a job"""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status != JobStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not in pending state"
        )
    
    # Store watermark selection data
    job.watermark_selections = json.dumps(watermark_data)
    db.commit()
    
    return {"message": "Watermark selection saved", "job_id": job_id}

@app.get("/api/jobs/{job_id}/watermarks")
def get_watermark_selections(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get watermark selections for a job"""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.watermark_selections:
        return json.loads(job.watermark_selections)
    else:
        return {"watermarks": []}

@app.post("/api/jobs/{job_id}/process")
def start_processing(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start processing a job with watermark removal"""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status != JobStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not in pending state"
        )
    
    # Start processing
    job.status = JobStatus.PROCESSING
    job.processing_started_at = datetime.utcnow()
    db.commit()
    
    # Process using FFmpeg delogo in background thread
    import threading
    def process_video_async():
        from app.database import SessionLocal
        background_db = SessionLocal()
        try:
            bg_job = background_db.query(Job).filter(Job.id == job.id).first()
            if not bg_job:
                return
            try:
                out_path = process_video_with_delogo(
                    original_file_path=bg_job.original_file_path,
                    processed_file_path=bg_job.processed_file_path,
                    watermark_selections_json=bg_job.watermark_selections,
                    user_id=bg_job.user_id,
                )
                bg_job.status = JobStatus.COMPLETED
                bg_job.processed_file_path = out_path
                bg_job.processing_completed_at = datetime.utcnow()
                background_db.commit()
                print(f"✅ Job {bg_job.id} processing completed: {out_path}")
            except Exception as e:
                bg_job.status = JobStatus.FAILED
                bg_job.error_message = str(e)
                background_db.commit()
                print(f"❌ Job {bg_job.id} processing failed: {e}")
        finally:
            background_db.close()
    
    thread = threading.Thread(target=process_video_async)
    thread.start()
    
    return {"message": "Processing started", "job_id": job_id}

# Serve video files (public endpoint for downloads)
@app.get("/api/videos/{job_id}/stream")
def stream_video(
    job_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Stream video file for viewing in browser (public endpoint)

    Query params:
    - preview=1 -> serve a blurred, lower-res preview suitable for anonymous users
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Allow streaming for watermark selection even if not completed
    if job.status not in [JobStatus.COMPLETED, JobStatus.PROCESSING, JobStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job not available for streaming"
        )
    
    # Build candidate keys with processed first
    candidate_keys = []
    if getattr(job, "processed_file_path", None):
        candidate_keys.append(job.processed_file_path)
    if getattr(job, "original_file_path", None):
        candidate_keys.append(job.original_file_path)
    
    # Skip S3 for localhost development - always use local storage
    # In production, enable S3 by setting USE_S3=true in environment
    use_s3 = os.getenv("USE_S3", "false").lower() == "true"
    if use_s3:
        for key in candidate_keys:
            if key and str(key).startswith("uploads/"):
                try:
                    url = s3_service.generate_presigned_url(key, expiration=3600)
                    if url:
                        print(f"✅ Redirecting to S3 for streaming: {key}")
                        return RedirectResponse(url=url, status_code=302)
                except Exception as e:
                    print(f"⚠️ S3 presign failed for {key}, will try local: {e}")
                    break
    else:
        print("📁 Using local storage for streaming (S3 disabled)")

    # Resolve the actual file path we can stream locally (fallback)
    file_path = None
    
    # Try direct absolute paths first (if any were stored as absolute)
    for key in candidate_keys:
        if os.path.isabs(key) and os.path.exists(key):
            file_path = key
            print(f"✅ Using absolute file path: {file_path}")
            break
    
    # If not absolute, search local_storage by filename match
    if not file_path:
        print(f"Searching local_storage for: {candidate_keys}")
        filenames = {os.path.basename(k) for k in candidate_keys if isinstance(k, str)}
        for root, dirs, files in os.walk("local_storage"):
            for name in files:
                if name in filenames:
                    candidate = os.path.join(root, name)
                    if os.path.exists(candidate):
                        file_path = candidate
                        print(f"✅ Found file in local storage: {file_path}")
                        break
            if file_path:
                break

    # Fallback: search user's directory (paid/free) for latest file
    if not file_path:
        try:
            storage_root = os.path.join("local_storage", "uploads")
            bucket_type = "paid" if any("/paid/" in k for k in candidate_keys if isinstance(k, str)) else "free"
            user_dir = os.path.join(storage_root, bucket_type, str(job.user_id))
            if os.path.isdir(user_dir):
                candidates = [
                    os.path.join(user_dir, f)
                    for f in os.listdir(user_dir)
                    if os.path.isfile(os.path.join(user_dir, f)) and f.lower().endswith(".mp4")
                ]
                if candidates:
                    # Pick most recently modified
                    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                    file_path = candidates[0]
                    print(f"✅ Fallback picked latest user file: {file_path}")
        except Exception as e:
            print(f"⚠️ Fallback user-dir search failed: {e}")
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found"
        )

    # If preview is requested, generate or reuse a blurred preview file
    preview_flag = request.query_params.get("preview")
    if preview_flag and preview_flag not in ("0", "false", "False"): 
        try:
            preview_dir = os.path.join("local_storage", "previews")
            os.makedirs(preview_dir, exist_ok=True)
            preview_path = os.path.join(preview_dir, f"{job.id}.mp4")

            # Recreate if missing or older than source
            need_generate = True
            if os.path.exists(preview_path):
                try:
                    need_generate = os.path.getmtime(preview_path) < os.path.getmtime(file_path)
                except Exception:
                    need_generate = False

            if need_generate:
                ffmpeg_bin = os.getenv("FFMPEG_BIN", "ffmpeg")
                # Build conservative blur + scale filter for legibility while obscuring content
                vf = "scale=min(720,iw):-2,boxblur=10:2"
                cmd = [
                    ffmpeg_bin, "-y", "-i", file_path,
                    "-vf", vf,
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
                    "-c:a", "aac", "-movflags", "+faststart",
                    preview_path,
                ]
                print(f"▶️ Generating preview: {' '.join(cmd)}")
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)

            # Serve the preview file instead
            file_path = preview_path
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Preview generation failed, falling back to original/processed: {e}")
        except Exception as e:
            print(f"⚠️ Preview error: {e}")
    
    # Byte-range support for reliable playback
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")
    if range_header:
        try:
            # Example: bytes=0- or bytes=1000-2000
            _, bytes_range = range_header.strip().split("=")
            start_str, end_str = bytes_range.split("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            start = max(0, start)
            end = min(file_size - 1, end)
            chunk_size = (end - start) + 1
        except Exception:
            start, end = 0, file_size - 1
            chunk_size = file_size

        def iter_file(path: str, offset: int, length: int, block_size: int = 1024 * 1024):
            with open(path, "rb") as f:
                f.seek(offset)
                remaining = length
                while remaining > 0:
                    read_size = min(block_size, remaining)
                    data = f.read(read_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(iter_file(file_path, start, chunk_size), status_code=206, headers=headers)

    # No range header: return full file
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }
    return FileResponse(file_path, media_type="video/mp4", headers=headers)

# ===== STRIPE PAYMENT ENDPOINTS =====

# Create Stripe checkout session
@app.post("/api/stripe/create-checkout")
def create_checkout_session(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Get the price ID based on the plan
        price_id = None
        if subscription_data.price_id == "monthly":
            price_id = STRIPE_PRICE_IDS["monthly"]
        elif subscription_data.price_id == "yearly":
            price_id = STRIPE_PRICE_IDS["yearly"]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid price ID"
            )
        
        # Create or get Stripe customer
        stripe_customer_id = current_user.stripe_customer_id
        if not stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": str(current_user.id)}
            )
            stripe_customer_id = customer.id
            
            # Update user with Stripe customer ID
            current_user.stripe_customer_id = stripe_customer_id
            db.commit()
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard?success=true",
            cancel_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/pricing?canceled=true",
            metadata={
                "user_id": str(current_user.id),
                "plan": subscription_data.price_id
            }
        )
        
        return {"checkout_url": checkout_session.url}
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# Handle successful payment
@app.get("/api/stripe/success")
def payment_success(session_id: str, db: Session = Depends(get_db)):
    try:
        # Retrieve the checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == "paid":
            # Get user from metadata
            user_id = session.metadata.get("user_id")
            plan = session.metadata.get("plan")
            
            if user_id:
                user = db.query(User).filter(User.id == int(user_id)).first()
                if user:
                    # Update subscription tier and allocate credits
                    if plan == "monthly":
                        user.subscription_tier = SubscriptionTier.MONTHLY
                        user.subscription_expires_at = datetime.utcnow() + timedelta(days=30)
                        user.credits += SUBSCRIPTION_CREDITS["monthly"]
                        user.monthly_credits = SUBSCRIPTION_CREDITS["monthly"]
                        user.last_credit_refill = datetime.utcnow()
                        print(f"✅ Allocated {SUBSCRIPTION_CREDITS['monthly']} credits to user {user.id}")
                    elif plan == "yearly":
                        user.subscription_tier = SubscriptionTier.YEARLY
                        user.subscription_expires_at = datetime.utcnow() + timedelta(days=365)
                        user.credits += SUBSCRIPTION_CREDITS["yearly"]
                        user.yearly_credits = SUBSCRIPTION_CREDITS["yearly"]
                        user.last_credit_refill = datetime.utcnow()
                        print(f"✅ Allocated {SUBSCRIPTION_CREDITS['yearly']} credits to user {user.id}")
                    
                    db.commit()
                    
                    return RedirectResponse(
                        url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard?subscription=success"
                    )
        
        return RedirectResponse(
            url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/pricing?error=payment_failed"
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/pricing?error=server_error"
        )

# Handle Stripe webhooks
@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        customer_id = subscription['customer']
        
        # Find user by Stripe customer ID
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            if subscription['status'] == 'active':
                # Subscription is active
                if subscription['items']['data'][0]['price']['id'] == STRIPE_PRICE_IDS["monthly"]:
                    user.subscription_tier = SubscriptionTier.MONTHLY
                elif subscription['items']['data'][0]['price']['id'] == STRIPE_PRICE_IDS["yearly"]:
                    user.subscription_tier = SubscriptionTier.YEARLY
            else:
                # Subscription is inactive/canceled
                user.subscription_tier = SubscriptionTier.FREE
            
            db.commit()
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription['customer']
        
        # Find user and downgrade to free
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.subscription_tier = SubscriptionTier.FREE
            user.subscription_expires_at = None
            db.commit()
    
    return {"status": "success"}

# Get user subscription status
@app.get("/api/subscription/status", response_model=SubscriptionResponse)
def get_subscription_status(
    current_user: User = Depends(get_current_active_user)
):
    # For admin users, show unlimited credits
    if current_user.is_admin:
        return SubscriptionResponse(
            subscription_tier=current_user.subscription_tier,
            expires_at=current_user.subscription_expires_at,
            credits=999999,  # Show unlimited for admin
            monthly_credits=current_user.monthly_credits,
            yearly_credits=current_user.yearly_credits
        )
    else:
        return SubscriptionResponse(
            subscription_tier=current_user.subscription_tier,
            expires_at=current_user.subscription_expires_at,
            credits=current_user.credits,
            monthly_credits=current_user.monthly_credits,
            yearly_credits=current_user.yearly_credits
        )

# Cancel subscription
@app.post("/api/subscription/cancel")
def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found"
        )
    
    try:
        # Get customer's subscriptions
        subscriptions = stripe.Subscription.list(
            customer=current_user.stripe_customer_id,
            status='active'
        )
        
        if subscriptions.data:
            # Cancel the first active subscription
            stripe.Subscription.modify(
                subscriptions.data[0].id,
                cancel_at_period_end=True
            )
            
            return {"message": "Subscription will be canceled at the end of the current period"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription found"
            )
            
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )

# ===== CREDIT SYSTEM ENDPOINTS =====

# Get available credit packs
@app.get("/api/credits/packs", response_model=List[CreditPack])
def get_credit_packs():
    """Get available credit packs for purchase"""
    return [CreditPack(**pack) for pack in CREDIT_PACKS]

# Get user's current credits
@app.get("/api/credits/status", response_model=UserCreditsResponse)
def get_user_credits(current_user: User = Depends(get_current_active_user)):
    """Get user's current credit status"""
    # For admin users, show unlimited credits
    if current_user.is_admin:
        return UserCreditsResponse(
            credits=999999,  # Show unlimited for admin
            monthly_credits=current_user.monthly_credits,
            yearly_credits=current_user.yearly_credits,
            last_credit_refill=current_user.last_credit_refill
        )
    else:
        return UserCreditsResponse(
            credits=current_user.credits,
            monthly_credits=current_user.monthly_credits,
            yearly_credits=current_user.yearly_credits,
            last_credit_refill=current_user.last_credit_refill
        )

# Purchase credits
@app.post("/api/credits/purchase")
def purchase_credits(
    purchase_data: CreditPurchaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe checkout session for credit purchase"""
    try:
        # Find the credit pack
        credit_pack = None
        for pack in CREDIT_PACKS:
            if pack["credits"] == purchase_data.credits:
                credit_pack = pack
                break
        
        if not credit_pack:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid credit pack"
            )
        
        # Create or get Stripe customer
        stripe_customer_id = current_user.stripe_customer_id
        if not stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": str(current_user.id)}
            )
            stripe_customer_id = customer.id
            current_user.stripe_customer_id = stripe_customer_id
            db.commit()
        
        # Create checkout session for one-time payment
        checkout_session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': credit_pack["name"],
                        'description': f"{credit_pack['credits']} processing credits"
                    },
                    'unit_amount': credit_pack["price"],
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard?credits=success",
            cancel_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/credits?canceled=true",
            metadata={
                "user_id": str(current_user.id),
                "credits": str(credit_pack["credits"]),
                "type": "credit_purchase"
            }
        )
        
        return {"checkout_url": checkout_session.url}
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# Handle successful credit purchase
@app.get("/api/credits/success")
def credit_purchase_success(session_id: str, db: Session = Depends(get_db)):
    """Handle successful credit purchase"""
    try:
        # Retrieve the checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == "paid":
            # Get user from metadata
            user_id = session.metadata.get("user_id")
            credits = int(session.metadata.get("credits", 0))
            
            if user_id and credits > 0:
                user = db.query(User).filter(User.id == int(user_id)).first()
                if user:
                    # Add credits to user account
                    user.credits += credits
                    db.commit()
                    
                    # Create credit purchase record
                    purchase = CreditPurchase(
                        user_id=user.id,
                        credits_purchased=credits,
                        amount_paid=session.amount_total,
                        currency=session.currency,
                        status="completed",
                        completed_at=datetime.utcnow()
                    )
                    db.add(purchase)
                    db.commit()
                    
                    print(f"✅ Added {credits} credits to user {user.id}. Total credits: {user.credits}")
                    
                    return RedirectResponse(
                        url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard?credits=success"
                    )
        
        return RedirectResponse(
            url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/credits?error=payment_failed"
        )
        
    except Exception as e:
        print(f"❌ Credit purchase success handler error: {e}")
        return RedirectResponse(
            url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/credits?error=server_error"
        )

# Get user's credit purchase history
@app.get("/api/credits/history", response_model=List[CreditPurchaseResponse])
def get_credit_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's credit purchase history"""
    purchases = db.query(CreditPurchase).filter(
        CreditPurchase.user_id == current_user.id
    ).order_by(CreditPurchase.created_at.desc()).all()
    
    return purchases

# Refill monthly credits (for cron job or manual trigger)
@app.post("/api/credits/refill")
def refill_monthly_credits(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Refill monthly credits for subscribed users"""
    if current_user.subscription_tier == SubscriptionTier.MONTHLY:
        # Check if it's time for monthly refill
        now = datetime.utcnow()
        if (not current_user.last_credit_refill or 
            (now - current_user.last_credit_refill).days >= 30):
            
            current_user.credits += current_user.monthly_credits
            current_user.last_credit_refill = now
            db.commit()
            
            return {
                "message": f"Refilled {current_user.monthly_credits} credits",
                "total_credits": current_user.credits
            }
        else:
            return {"message": "Monthly refill not yet due"}
    
    elif current_user.subscription_tier == SubscriptionTier.YEARLY:
        # Check if it's time for yearly refill
        now = datetime.utcnow()
        if (not current_user.last_credit_refill or 
            (now - current_user.last_credit_refill).days >= 365):
            
            current_user.credits += current_user.yearly_credits
            current_user.last_credit_refill = now
            db.commit()
            
            return {
                "message": f"Refilled {current_user.yearly_credits} credits",
                "total_credits": current_user.credits
            }
        else:
            return {"message": "Yearly refill not yet due"}
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription for credit refill"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
