from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import tempfile
import stripe
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
