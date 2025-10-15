"""
Upgrade User to Admin Script
Upgrades an existing user to admin with unlimited uploads
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
from sqlalchemy.orm import Session

def upgrade_user_to_admin(email: str):
    """Upgrade a user to admin status"""
    
    try:
        db = next(get_db())
        
        # Find the user
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User not found: {email}")
            return False
        
        # Upgrade to admin
        user.subscription_tier = SubscriptionTier.YEARLY
        user.subscription_expires_at = datetime.utcnow() + timedelta(days=365*10)  # 10 years
        user.is_active = True
        
        db.commit()
        
        print(f"✅ User upgraded to admin: {email}")
        print(f"👑 Subscription: {user.subscription_tier}")
        print(f"📅 Expires: {user.subscription_expires_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error upgrading user: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def upgrade_user_by_id(user_id: int):
    """Upgrade a user to admin by ID"""
    
    try:
        db = next(get_db())
        
        # Find the user
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            print(f"❌ User not found with ID: {user_id}")
            return False
        
        # Upgrade to admin
        user.subscription_tier = SubscriptionTier.YEARLY
        user.subscription_expires_at = datetime.utcnow() + timedelta(days=365*10)  # 10 years
        user.is_active = True
        
        db.commit()
        
        print(f"✅ User upgraded to admin: {user.email}")
        print(f"👑 Subscription: {user.subscription_tier}")
        print(f"📅 Expires: {user.subscription_expires_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error upgrading user: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def list_users_with_ids():
    """List all users with their IDs"""
    
    try:
        db = next(get_db())
        users = db.query(User).all()
        
        print("👥 All Users:")
        print("=" * 60)
        
        for user in users:
            print(f"🆔 ID: {user.id}")
            print(f"📧 Email: {user.email}")
            print(f"👑 Subscription: {user.subscription_tier}")
            print(f"📅 Created: {user.created_at}")
            print(f"✅ Active: {user.is_active}")
            print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("🚀 Sora Watermark Remover - User Upgrade Tool")
    print("=" * 50)
    
    while True:
        print("\nChoose an option:")
        print("1. Upgrade user by email")
        print("2. Upgrade user by ID")
        print("3. List all users")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            email = input("Enter user email: ").strip()
            if email:
                upgrade_user_to_admin(email)
        elif choice == "2":
            try:
                user_id = int(input("Enter user ID: ").strip())
                upgrade_user_by_id(user_id)
            except ValueError:
                print("❌ Invalid user ID")
        elif choice == "3":
            list_users_with_ids()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
