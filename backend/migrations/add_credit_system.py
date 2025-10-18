#!/usr/bin/env python3
"""
Migration script to add credit system columns to the users table
and create the credit_purchases table.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine

def run_migration():
    """Add credit system columns and tables"""
    try:
        with engine.connect() as connection:
            # Add credit columns to users table
            print("🔄 Adding credit system columns to users table...")
            
            # Check if columns already exist
            check_columns_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name IN ('credits', 'monthly_credits', 'yearly_credits', 'last_credit_refill');
            """
            
            result = connection.execute(text(check_columns_sql))
            existing_columns = [row[0] for row in result]
            
            # Add credits column
            if 'credits' not in existing_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 0;"))
                print("✅ Added credits column")
            else:
                print("✅ credits column already exists")
            
            # Add monthly_credits column
            if 'monthly_credits' not in existing_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN monthly_credits INTEGER DEFAULT 0;"))
                print("✅ Added monthly_credits column")
            else:
                print("✅ monthly_credits column already exists")
            
            # Add yearly_credits column
            if 'yearly_credits' not in existing_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN yearly_credits INTEGER DEFAULT 0;"))
                print("✅ Added yearly_credits column")
            else:
                print("✅ yearly_credits column already exists")
            
            # Add last_credit_refill column
            if 'last_credit_refill' not in existing_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN last_credit_refill TIMESTAMP;"))
                print("✅ Added last_credit_refill column")
            else:
                print("✅ last_credit_refill column already exists")
            
            # Create credit_purchases table
            print("🔄 Creating credit_purchases table...")
            
            create_credit_purchases_sql = """
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
            );
            """
            
            connection.execute(text(create_credit_purchases_sql))
            print("✅ Created credit_purchases table")
            
            connection.commit()
            print("🎉 Credit system migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
