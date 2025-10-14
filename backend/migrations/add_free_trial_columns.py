"""
Database migration to add free trial tracking columns
Run this script to update your database schema
"""

from sqlalchemy import create_engine, text
from app.database import engine
import os

def run_migration():
    """Add free trial columns to users table"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./local_test.db')
    
    # Create engine
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as connection:
            # Add new columns to users table
            migration_sql = """
            ALTER TABLE users ADD COLUMN free_uploads_used INTEGER DEFAULT 0;
            ALTER TABLE users ADD COLUMN free_uploads_limit INTEGER DEFAULT 1;
            ALTER TABLE users ADD COLUMN last_free_upload_at DATETIME;
            """
            
            # Execute migration
            connection.execute(text(migration_sql))
            connection.commit()
            
            print("✅ Migration completed successfully!")
            print("Added columns:")
            print("  - free_uploads_used (INTEGER, default 0)")
            print("  - free_uploads_limit (INTEGER, default 1)")
            print("  - last_free_upload_at (DATETIME)")
            
    except Exception as e:
        if "duplicate column name" in str(e):
            print("✅ Columns already exist - migration not needed")
        else:
            print(f"❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    run_migration()
