#!/usr/bin/env python3
"""
Simple migration script to add credit system columns to the users table
and create the credit_purchases table.
"""

import os
import sys
import sqlite3
import psycopg2
from urllib.parse import urlparse

def get_database_url():
    """Get database URL from environment"""
    # Try different environment variable names
    db_url = os.getenv('DATABASE_URL') or os.getenv('DB_URL') or os.getenv('DB_CONNECTION_STRING')
    
    if not db_url:
        # Default to SQLite for local development
        return 'sqlite:///local_test.db'
    
    return db_url

def run_sqlite_migration(db_path):
    """Run migration for SQLite database"""
    print(f"Running SQLite migration on {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add credits column
        if 'credits' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 0")
            print("Added credits column")
        else:
            print("credits column already exists")
        
        # Add monthly_credits column
        if 'monthly_credits' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN monthly_credits INTEGER DEFAULT 0")
            print("Added monthly_credits column")
        else:
            print("monthly_credits column already exists")
        
        # Add yearly_credits column
        if 'yearly_credits' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN yearly_credits INTEGER DEFAULT 0")
            print("Added yearly_credits column")
        else:
            print("yearly_credits column already exists")
        
        # Add last_credit_refill column
        if 'last_credit_refill' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_credit_refill TIMESTAMP")
            print("Added last_credit_refill column")
        else:
            print("last_credit_refill column already exists")
        
        # Create credit_purchases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stripe_payment_intent_id VARCHAR(255),
                credits_purchased INTEGER NOT NULL,
                amount_paid INTEGER NOT NULL,
                currency VARCHAR(10) DEFAULT 'usd',
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        print("Created credit_purchases table")
        
        conn.commit()
        print("SQLite migration completed successfully!")
        
    except Exception as e:
        print(f"SQLite migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def run_postgres_migration(db_url):
    """Run migration for PostgreSQL database"""
    print(f"Running PostgreSQL migration")
    
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name IN ('credits', 'monthly_credits', 'yearly_credits', 'last_credit_refill');
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add credits column
        if 'credits' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 0")
            print("Added credits column")
        else:
            print("credits column already exists")
        
        # Add monthly_credits column
        if 'monthly_credits' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN monthly_credits INTEGER DEFAULT 0")
            print("Added monthly_credits column")
        else:
            print("monthly_credits column already exists")
        
        # Add yearly_credits column
        if 'yearly_credits' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN yearly_credits INTEGER DEFAULT 0")
            print("Added yearly_credits column")
        else:
            print("yearly_credits column already exists")
        
        # Add last_credit_refill column
        if 'last_credit_refill' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_credit_refill TIMESTAMP")
            print("Added last_credit_refill column")
        else:
            print("last_credit_refill column already exists")
        
        # Create credit_purchases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_purchases (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                stripe_payment_intent_id VARCHAR(255),
                credits_purchased INTEGER NOT NULL,
                amount_paid INTEGER NOT NULL,
                currency VARCHAR(10) DEFAULT 'usd',
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        print("Created credit_purchases table")
        
        conn.commit()
        print("PostgreSQL migration completed successfully!")
        
    except Exception as e:
        print(f"PostgreSQL migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def main():
    """Run the appropriate migration based on database type"""
    db_url = get_database_url()
    
    if db_url.startswith('sqlite'):
        # Extract SQLite file path
        if db_url == 'sqlite:///local_test.db':
            db_path = 'local_test.db'
        else:
            db_path = db_url.replace('sqlite:///', '')
        
        if not os.path.exists(db_path):
            print(f"SQLite database file not found: {db_path}")
            print("Please create the database first by running your application.")
            return
        
        run_sqlite_migration(db_path)
        
    elif db_url.startswith('postgresql'):
        run_postgres_migration(db_url)
        
    else:
        print(f"Unsupported database URL: {db_url}")
        print("Supported databases: SQLite, PostgreSQL")
        sys.exit(1)

if __name__ == "__main__":
    main()
