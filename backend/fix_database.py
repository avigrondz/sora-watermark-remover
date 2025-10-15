"""
Fix Database - Add watermark_selections column
"""

import sqlite3
import os
from pathlib import Path

def fix_database():
    """Add the missing watermark_selections column to the jobs table"""
    
    # Find the database file
    db_path = Path("local_test.db")
    if not db_path.exists():
        print("Database file not found!")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'watermark_selections' in columns:
            print("Column 'watermark_selections' already exists!")
            return True
        
        # Add the column
        print("Adding watermark_selections column...")
        cursor.execute("ALTER TABLE jobs ADD COLUMN watermark_selections TEXT")
        conn.commit()
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'watermark_selections' in columns:
            print("+ Column 'watermark_selections' added successfully!")
            return True
        else:
            print("X Failed to add column")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if fix_database():
        print("Database fixed successfully!")
    else:
        print("Failed to fix database")
