#!/usr/bin/env python3
"""
Fix enum values in the database to use correct case.
"""

import sqlite3
import os

def fix_enum_values():
    """Fix enum values in the database"""
    db_path = "local_test.db"
    
    if not os.path.exists(db_path):
        print("Database file not found.")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Fix subscription_tier values
        print("Fixing subscription_tier values...")
        
        # Update 'free' to 'FREE'
        cursor.execute("UPDATE users SET subscription_tier = 'FREE' WHERE subscription_tier = 'free'")
        print(f"Updated {cursor.rowcount} users from 'free' to 'FREE'")
        
        # Update 'monthly' to 'MONTHLY'
        cursor.execute("UPDATE users SET subscription_tier = 'MONTHLY' WHERE subscription_tier = 'monthly'")
        print(f"Updated {cursor.rowcount} users from 'monthly' to 'MONTHLY'")
        
        # Update 'yearly' to 'YEARLY'
        cursor.execute("UPDATE users SET subscription_tier = 'YEARLY' WHERE subscription_tier = 'yearly'")
        print(f"Updated {cursor.rowcount} users from 'yearly' to 'YEARLY'")
        
        conn.commit()
        print("Enum values fixed successfully!")
        return True
        
    except Exception as e:
        print(f"Error fixing enum values: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Fix enum values in database"""
    print("Fixing enum values in database...")
    
    if fix_enum_values():
        print("Database enum values fixed successfully!")
    else:
        print("Failed to fix enum values")

if __name__ == "__main__":
    main()
