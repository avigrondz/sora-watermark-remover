from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import RedirectResponse, FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import tempfile
import stripe
from datetime import datetime, timedelta
import json

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
from services.local_storage import local_storage
from services.video_processor import process_video_with_delogo

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Stripe price IDs (you'll need to create these in your Stripe dashboard)
STRIPE_PRICE_IDS = {
    "monthly": os.getenv("STRIPE_MONTHLY_PRICE_ID", "price_monthly_placeholder"),
    "yearly": os.getenv("STRIPE_YEARLY_PRICE_ID", "price_yearly_placeholder")
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

# Upload video for processing
@app.post("/api/videos/upload", response_model=VideoUploadResponse)
def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check free trial limits for free users
    if current_user.subscription_tier == SubscriptionTier.FREE:
        # Count existing jobs for this user (simple approach)
        existing_jobs = db.query(Job).filter(Job.user_id == current_user.id).count()
        if existing_jobs >= 1:  # 1 free upload limit
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free trial limit reached. Please subscribe to continue."
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
    """Stream video file for viewing in browser (public endpoint)"""
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
    
    # If processed file is on S3, redirect to presigned URL immediately
    if getattr(job, "processed_file_path", None) and str(job.processed_file_path).startswith("uploads/"):
        try:
            url = s3_service.generate_presigned_url(job.processed_file_path, expiration=3600)
            if url:
                print(f"✅ Redirecting to S3 processed file for streaming: {job.processed_file_path}")
                return RedirectResponse(url=url, status_code=302)
        except Exception as e:
            print(f"⚠️ S3 presign failed for processed file, will try local: {e}")

    # Resolve the actual file path we can stream (prefer processed over original)
    file_path = None
    
    # Build candidate keys with processed first
    candidate_keys = []
    if getattr(job, "processed_file_path", None):
        candidate_keys.append(job.processed_file_path)
    if getattr(job, "original_file_path", None):
        candidate_keys.append(job.original_file_path)
    
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
    return FileResponse(file_path, media_type="video/mp4")

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
                    # Update subscription tier
                    if plan == "monthly":
                        user.subscription_tier = SubscriptionTier.MONTHLY
                        user.subscription_expires_at = datetime.utcnow() + timedelta(days=30)
                    elif plan == "yearly":
                        user.subscription_tier = SubscriptionTier.YEARLY
                        user.subscription_expires_at = datetime.utcnow() + timedelta(days=365)
                    
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
    return SubscriptionResponse(
        subscription_tier=current_user.subscription_tier,
        expires_at=current_user.subscription_expires_at
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
