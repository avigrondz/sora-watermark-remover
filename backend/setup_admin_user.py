#!/usr/bin/env python3
"""
Script to create admin user and add is_admin column to database.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def add_admin_column():
    """Add is_admin column to users table"""
    db_path = "local_test.db"
    
    if not os.path.exists(db_path):
        print("Database file not found. Please run the application first to create the database.")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if is_admin column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_admin' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            print("Added is_admin column to users table")
        else:
            print("is_admin column already exists")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error adding is_admin column: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def create_admin_user():
    """Create admin user if it doesn't exist"""
    from app.database import SessionLocal
    from app.models import User
    from app.auth import get_password_hash
    
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.email == "admin@sorawatermarks.com").first()
        
        if admin_user:
            # Update existing user to be admin
            admin_user.is_admin = True
            admin_user.credits = 999999  # Give admin unlimited credits
            admin_user.subscription_tier = "FREE"  # Keep as free tier but with admin privileges
            db.commit()
            print("Updated existing admin user with admin privileges")
        else:
            # Create new admin user
            admin_user = User(
                email="admin@sorawatermarks.com",
                hashed_password=get_password_hash("admin123"),  # Default password
                is_admin=True,
                credits=999999,  # Unlimited credits
                subscription_tier="FREE",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("Created new admin user: admin@sorawatermarks.com")
            print("Default password: admin123")
            print("Please change the password after first login!")
        
        return True
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Setup admin user and database"""
    print("Setting up admin user...")
    
    # Add is_admin column
    if not add_admin_column():
        print("Failed to add is_admin column")
        return
    
    # Create admin user
    if not create_admin_user():
        print("Failed to create admin user")
        return
    
    print("\nAdmin setup completed!")
    print("Admin email: admin@sorawatermarks.com")
    print("Admin password: admin123")
    print("Admin users have unlimited credits and can process videos without restrictions.")

if __name__ == "__main__":
    main()
