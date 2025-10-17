#!/usr/bin/env python3
"""
Database migration runner for Railway deployment
This script applies the watermark_selections column migration
"""

import os
import sys
from sqlalchemy import create_engine, text

def run_watermark_migration():
    """Add watermark_selections column to jobs table"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    print(f"🔗 Connecting to database...")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Check if column already exists
            check_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'jobs' AND column_name = 'watermark_selections';
            """
            
            result = connection.execute(text(check_sql))
            existing_columns = [row[0] for row in result]
            
            if 'watermark_selections' in existing_columns:
                print("✅ watermark_selections column already exists - migration not needed")
                return True
            
            # Add watermark_selections column to jobs table
            migration_sql = """
            ALTER TABLE jobs ADD COLUMN watermark_selections TEXT;
            """
            
            print("🔄 Adding watermark_selections column...")
            connection.execute(text(migration_sql))
            connection.commit()
            
            print("✅ Migration completed successfully!")
            print("Added column: watermark_selections (TEXT, nullable)")
            return True
            
    except Exception as e:
        error_msg = str(e).lower()
        if "duplicate column name" in error_msg or "column already exists" in error_msg:
            print("✅ Column already exists - migration not needed")
            return True
        else:
            print(f"❌ Migration failed: {str(e)}")
            return False

if __name__ == "__main__":
    success = run_watermark_migration()
    sys.exit(0 if success else 1)
