#!/usr/bin/env python3
"""
Test script to verify Stripe integration and credit system setup.
Run this after setting up your Stripe products and environment variables.
"""

import os
import sys
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_stripe_configuration():
    """Test that all required Stripe configuration is present"""
    print("🔍 Testing Stripe Configuration...")
    
    required_vars = [
        'STRIPE_SECRET_KEY',
        'STRIPE_PUBLISHABLE_KEY', 
        'STRIPE_WEBHOOK_SECRET',
        'STRIPE_MONTHLY_PRICE_ID',
        'STRIPE_YEARLY_PRICE_ID',
        'STRIPE_CREDITS_10_PRICE_ID',
        'STRIPE_CREDITS_25_PRICE_ID',
        'STRIPE_CREDITS_50_PRICE_ID',
        'STRIPE_CREDITS_100_PRICE_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def test_stripe_connection():
    """Test connection to Stripe API"""
    print("\n🔍 Testing Stripe API Connection...")
    
    try:
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        # Test API connection by retrieving account info
        account = stripe.Account.retrieve()
        print(f"✅ Connected to Stripe account: {account.display_name or account.id}")
        
        # Check if we're in test mode
        if account.livemode:
            print("⚠️  WARNING: You're using LIVE mode! Make sure this is intended for production.")
        else:
            print("✅ Using test mode (safe for development)")
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Stripe: {e}")
        return False

def test_price_ids():
    """Test that all price IDs are valid"""
    print("\n🔍 Testing Price IDs...")
    
    price_ids = {
        'Monthly': os.getenv('STRIPE_MONTHLY_PRICE_ID'),
        'Yearly': os.getenv('STRIPE_YEARLY_PRICE_ID'),
        'Credits 10': os.getenv('STRIPE_CREDITS_10_PRICE_ID'),
        'Credits 25': os.getenv('STRIPE_CREDITS_25_PRICE_ID'),
        'Credits 50': os.getenv('STRIPE_CREDITS_50_PRICE_ID'),
        'Credits 100': os.getenv('STRIPE_CREDITS_100_PRICE_ID'),
    }
    
    all_valid = True
    
    for name, price_id in price_ids.items():
        try:
            price = stripe.Price.retrieve(price_id)
            print(f"✅ {name}: {price.nickname or price.product} - ${price.unit_amount/100:.2f}")
        except Exception as e:
            print(f"❌ {name}: Invalid price ID - {e}")
            all_valid = False
    
    return all_valid

def test_webhook_endpoint():
    """Test webhook endpoint configuration"""
    print("\n🔍 Testing Webhook Configuration...")
    
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    if not webhook_secret:
        print("❌ No webhook secret configured")
        return False
    
    if not webhook_secret.startswith('whsec_'):
        print("❌ Invalid webhook secret format")
        return False
    
    print("✅ Webhook secret is properly configured")
    return True

def main():
    """Run all tests"""
    print("🚀 Stripe Integration Test Suite")
    print("=" * 50)
    
    tests = [
        test_stripe_configuration,
        test_stripe_connection,
        test_price_ids,
        test_webhook_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Stripe integration is ready.")
        print("\nNext steps:")
        print("1. Run the database migration: python migrations/add_credit_system.py")
        print("2. Start your application")
        print("3. Test the payment flow in your browser")
    else:
        print("❌ Some tests failed. Please fix the issues above before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
