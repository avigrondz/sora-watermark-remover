#!/usr/bin/env python3
"""
Setup development environment with minimal dependencies.
This script creates a basic environment file for local development.
"""

import os
from pathlib import Path

def create_dev_env():
    """Create a development environment file"""
    env_content = """# Development Environment Configuration
# This file is for local development only

# Database (SQLite for local development)
DATABASE_URL=sqlite:///local_test.db

# Stripe Configuration (Test Mode)
# Replace these with your actual Stripe test keys
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Subscription Price IDs (Test Mode)
# Replace these with your actual Stripe test price IDs
STRIPE_MONTHLY_PRICE_ID=price_test_monthly_placeholder
STRIPE_YEARLY_PRICE_ID=price_test_yearly_placeholder

# Credit Pack Price IDs (Test Mode)
STRIPE_CREDITS_10_PRICE_ID=price_test_credits_10_placeholder
STRIPE_CREDITS_25_PRICE_ID=price_test_credits_25_placeholder
STRIPE_CREDITS_50_PRICE_ID=price_test_credits_50_placeholder
STRIPE_CREDITS_100_PRICE_ID=price_test_credits_100_placeholder

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Storage (Local for development)
USE_S3=false

# Security
SECRET_KEY=your-secret-key-for-development-only
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
"""

    env_file = Path("config.dev.env")
    
    if env_file.exists():
        print("✅ Development environment file already exists")
        return
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print("Created development environment file: config.dev.env")
    print("Please update the Stripe keys and price IDs in config.dev.env")

def main():
    """Setup development environment"""
    print("Setting up development environment...")
    
    # Create development environment file
    create_dev_env()
    
    print("\nNext steps:")
    print("1. Update config.dev.env with your Stripe test keys")
    print("2. Run: python start_dev_simple.py")
    print("3. Open http://localhost:8000/docs to test the API")

if __name__ == "__main__":
    main()
