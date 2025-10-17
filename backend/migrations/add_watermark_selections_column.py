"""
Database migration to add watermark_selections column to jobs table
Run this script to update your database schema
"""

from sqlalchemy import create_engine, text
import os

def run_migration():
    """Add watermark_selections column to jobs table"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./local_test.db')
    
    # Create engine
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as connection:
            # Add watermark_selections column to jobs table
            migration_sql = """
            ALTER TABLE jobs ADD COLUMN watermark_selections TEXT;
            """
            
            # Execute migration
            connection.execute(text(migration_sql))
            connection.commit()
            
            print("✅ Migration completed successfully!")
            print("Added column:")
            print("  - watermark_selections (TEXT, nullable)")
            
    except Exception as e:
        if "duplicate column name" in str(e) or "column already exists" in str(e).lower():
            print("✅ Column already exists - migration not needed")
        else:
            print(f"❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    run_migration()
