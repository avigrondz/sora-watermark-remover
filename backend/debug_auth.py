"""
Debug Authentication Issues
This script will help diagnose login problems
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import get_db, engine
from app.models import Base, User, SubscriptionTier
from app.auth import get_password_hash, verify_password
from sqlalchemy.orm import Session

def check_database():
    """Check if database and tables exist"""
    
    try:
        # Create database tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def list_all_users():
    """List all users in the database"""
    
    try:
        db = next(get_db())
        users = db.query(User).all()
        
        print(f"\n👥 Found {len(users)} users in database:")
        print("=" * 50)
        
        for user in users:
            print(f"🆔 ID: {user.id}")
            print(f"📧 Email: {user.email}")
            print(f"👑 Subscription: {user.subscription_tier}")
            print(f"✅ Active: {user.is_active}")
            print(f"📅 Created: {user.created_at}")
            print("-" * 30)
        
        return users
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return []
    finally:
        if 'db' in locals():
            db.close()

def create_admin_user():
    """Create admin user with proper setup"""
    
    try:
        db = next(get_db())
        
        admin_email = "admin@sorawatermarks.com"
        admin_password = "admin123"
        
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        
        if existing_admin:
            print(f"⚠️  Admin user already exists: {admin_email}")
            print("🔄 Updating admin user...")
            
            # Update existing admin
            existing_admin.hashed_password = get_password_hash(admin_password)
            existing_admin.subscription_tier = SubscriptionTier.YEARLY
            existing_admin.is_active = True
            existing_admin.subscription_expires_at = None  # No expiration for admin
            
            db.commit()
            print("✅ Admin user updated successfully!")
        else:
            print("🆕 Creating new admin user...")
            
            # Create new admin user
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                is_active=True,
                subscription_tier=SubscriptionTier.YEARLY,
                subscription_expires_at=None,  # No expiration for admin
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            print("✅ Admin user created successfully!")
        
        print(f"📧 Email: {admin_email}")
        print(f"🔑 Password: {admin_password}")
        print(f"👑 Subscription: YEARLY (unlimited)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def test_password_verification():
    """Test password verification"""
    
    try:
        db = next(get_db())
        
        admin_email = "admin@sorawatermarks.com"
        admin_password = "admin123"
        
        # Find admin user
        admin_user = db.query(User).filter(User.email == admin_email).first()
        
        if not admin_user:
            print(f"❌ Admin user not found: {admin_email}")
            return False
        
        # Test password verification
        password_valid = verify_password(admin_password, admin_user.hashed_password)
        
        if password_valid:
            print("✅ Password verification successful!")
            print(f"👤 User: {admin_user.email}")
            print(f"👑 Subscription: {admin_user.subscription_tier}")
            print(f"✅ Active: {admin_user.is_active}")
            return True
        else:
            print("❌ Password verification failed!")
            print("🔄 Updating password...")
            
            # Update password
            admin_user.hashed_password = get_password_hash(admin_password)
            db.commit()
            
            print("✅ Password updated. Try logging in again.")
            return True
            
    except Exception as e:
        print(f"❌ Error testing password: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def reset_admin_password():
    """Reset admin password to ensure it works"""
    
    try:
        db = next(get_db())
        
        admin_email = "admin@sorawatermarks.com"
        new_password = "admin123"
        
        # Find admin user
        admin_user = db.query(User).filter(User.email == admin_email).first()
        
        if not admin_user:
            print(f"❌ Admin user not found: {admin_email}")
            return False
        
        # Reset password
        admin_user.hashed_password = get_password_hash(new_password)
        admin_user.is_active = True
        admin_user.subscription_tier = SubscriptionTier.YEARLY
        
        db.commit()
        
        print("✅ Admin password reset successfully!")
        print(f"📧 Email: {admin_email}")
        print(f"🔑 Password: {new_password}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("🔍 Sora Watermark Remover - Authentication Debug")
    print("=" * 60)
    
    # Step 1: Check database
    print("\n1️⃣ Checking database...")
    if not check_database():
        print("❌ Database setup failed")
        sys.exit(1)
    
    # Step 2: List users
    print("\n2️⃣ Checking existing users...")
    users = list_all_users()
    
    # Step 3: Create/update admin
    print("\n3️⃣ Setting up admin user...")
    if not create_admin_user():
        print("❌ Admin user setup failed")
        sys.exit(1)
    
    # Step 4: Test password
    print("\n4️⃣ Testing password verification...")
    if not test_password_verification():
        print("❌ Password verification failed")
        sys.exit(1)
    
    # Step 5: Reset password if needed
    print("\n5️⃣ Ensuring password works...")
    reset_admin_password()
    
    print("\n🎉 Authentication debug complete!")
    print("💡 Try logging in with:")
    print("   📧 Email: admin@sorawatermarks.com")
    print("   🔑 Password: admin123")
    print("\n🔧 If login still doesn't work, check:")
    print("   - Server is running on http://localhost:8000")
    print("   - Frontend is running on http://localhost:3000")
    print("   - Check browser console for errors")
