#!/usr/bin/env python3
"""
Database setup script for Sora Watermark Remover
This script creates the database tables and sets up the initial configuration.
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config.env")

def setup_database():
    """Set up the database tables"""
    try:
        # Import after loading environment variables
        from app.database import engine, Base
        from app.models import User, Job, SubscriptionTier, JobStatus
        
        print("🔧 Setting up database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database tables created successfully!")
        
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection test successful!")
            
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        print("\n🔍 Troubleshooting tips:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your DATABASE_URL in config.env")
        print("3. Ensure the database exists")
        print("4. Verify your database credentials")
        return False

def test_registration():
    """Test the registration endpoint"""
    try:
        from app.database import SessionLocal
        from app.models import User
        from app.auth import get_password_hash
        
        print("\n🧪 Testing user registration...")
        
        db = SessionLocal()
        try:
            # Test creating a user
            test_email = "test@example.com"
            test_password = "testpassword123"
            
            # Check if test user already exists
            existing_user = db.query(User).filter(User.email == test_email).first()
            if existing_user:
                db.delete(existing_user)
                db.commit()
                print("🗑️  Removed existing test user")
            
            # Create test user
            hashed_password = get_password_hash(test_password)
            test_user = User(
                email=test_email,
                hashed_password=hashed_password,
                subscription_tier=SubscriptionTier.FREE
            )
            
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            
            print(f"✅ Test user created successfully! ID: {test_user.id}")
            
            # Clean up test user
            db.delete(test_user)
            db.commit()
            print("🧹 Test user cleaned up")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Registration test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Sora Watermark Remover - Database Setup")
    print("=" * 50)
    
    # Check if config.env exists
    if not os.path.exists("config.env"):
        print("❌ config.env file not found!")
        print("Please create config.env with your database configuration.")
        sys.exit(1)
    
    # Setup database
    if setup_database():
        # Test registration
        if test_registration():
            print("\n🎉 Setup completed successfully!")
            print("Your registration should now work properly.")
        else:
            print("\n⚠️  Database setup succeeded but registration test failed.")
            print("Check your database configuration and try again.")
    else:
        print("\n❌ Setup failed. Please check your configuration and try again.")
        sys.exit(1)
