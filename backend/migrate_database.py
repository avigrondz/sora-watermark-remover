"""
Database Migration Script
Adds the new columns to the users table
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Add new columns to the users table"""
    
    # Get database path
    db_path = "local_test.db"
    if not os.path.exists(db_path):
        print("❌ Database file not found. Please run the server first to create it.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Migrating database...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add new columns if they don't exist
        new_columns = [
            ("free_uploads_used", "INTEGER DEFAULT 0"),
            ("free_uploads_limit", "INTEGER DEFAULT 1"),
            ("last_free_upload_at", "DATETIME")
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"⚠️  Column {column_name} already exists")
                    else:
                        print(f"❌ Error adding column {column_name}: {e}")
            else:
                print(f"✅ Column {column_name} already exists")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("🎉 Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Database Migration for Sora Watermark Remover")
    print("=" * 50)
    
    if migrate_database():
        print("\n✅ Migration successful!")
        print("💡 You can now restart your server")
    else:
        print("\n❌ Migration failed")
        print("💡 Try running the server first to create the database")
