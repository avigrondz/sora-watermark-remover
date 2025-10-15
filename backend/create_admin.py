"""
Create Admin User Script
Creates an admin user with unlimited uploads
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import get_db, engine
from app.models import Base, User, SubscriptionTier
from app.auth import get_password_hash
from sqlalchemy.orm import Session

def create_admin_user():
    """Create an admin user with unlimited uploads"""
    
    try:
        # Create database tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Get database session
        db = next(get_db())
        
        # Admin user details
        admin_email = "admin@sorawatermarks.com"
        admin_password = "admin123"  # Change this to a secure password
        
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        
        if existing_admin:
            print(f"✅ Admin user already exists: {admin_email}")
            print("💡 To reset password, delete the user first")
            return True
        
        # Create admin user
        admin_user = User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            is_active=True,
            subscription_tier=SubscriptionTier.YEARLY,  # Unlimited uploads
            subscription_expires_at=datetime.utcnow() + timedelta(days=365*10),  # 10 years
            created_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("🎉 Admin user created successfully!")
        print(f"📧 Email: {admin_email}")
        print(f"🔑 Password: {admin_password}")
        print(f"👑 Subscription: {admin_user.subscription_tier}")
        print(f"📅 Expires: {admin_user.subscription_expires_at}")
        print("\n💡 You can now login with these credentials")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def create_custom_admin():
    """Create a custom admin user with your own credentials"""
    
    print("🔧 Create Custom Admin User")
    print("=" * 40)
    
    email = input("Enter admin email: ").strip()
    if not email:
        print("❌ Email is required")
        return False
    
    password = input("Enter admin password: ").strip()
    if not password:
        print("❌ Password is required")
        return False
    
    try:
        # Create database tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Get database session
        db = next(get_db())
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            print(f"⚠️  User already exists: {email}")
            update = input("Update to admin? (y/n): ").strip().lower()
            if update == 'y':
                existing_user.subscription_tier = SubscriptionTier.YEARLY
                existing_user.subscription_expires_at = datetime.utcnow() + timedelta(days=365*10)
                existing_user.hashed_password = get_password_hash(password)
                db.commit()
                print("✅ User updated to admin")
                return True
            else:
                return False
        
        # Create admin user
        admin_user = User(
            email=email,
            hashed_password=get_password_hash(password),
            is_active=True,
            subscription_tier=SubscriptionTier.YEARLY,  # Unlimited uploads
            subscription_expires_at=datetime.utcnow() + timedelta(days=365*10),  # 10 years
            created_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("🎉 Custom admin user created successfully!")
        print(f"📧 Email: {email}")
        print(f"👑 Subscription: {admin_user.subscription_tier}")
        print(f"📅 Expires: {admin_user.subscription_expires_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def list_users():
    """List all users in the system"""
    
    try:
        db = next(get_db())
        users = db.query(User).all()
        
        print("👥 All Users:")
        print("=" * 50)
        
        for user in users:
            print(f"📧 Email: {user.email}")
            print(f"👑 Subscription: {user.subscription_tier}")
            print(f"📅 Created: {user.created_at}")
            print(f"✅ Active: {user.is_active}")
            print("-" * 30)
        
        return True
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("🚀 Sora Watermark Remover - Admin User Management")
    print("=" * 60)
    
    while True:
        print("\nChoose an option:")
        print("1. Create default admin user")
        print("2. Create custom admin user")
        print("3. List all users")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            create_admin_user()
        elif choice == "2":
            create_custom_admin()
        elif choice == "3":
            list_users()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
