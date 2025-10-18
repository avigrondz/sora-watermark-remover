#!/usr/bin/env python3
"""
Test script to verify admin user functionality.
"""

import requests
import json

def test_admin_login():
    """Test admin user login"""
    print("Testing admin user login...")
    
    login_data = {
        "email": "admin@sorawatermarks.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("Admin login successful!")
            print(f"Token: {data['access_token'][:20]}...")
            return data['access_token']
        else:
            print(f"Admin login failed: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"Error testing admin login: {e}")
        return None

def test_admin_credits(token):
    """Test admin user credits"""
    print("\nTesting admin user credits...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            "http://localhost:8000/api/credits/status",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print("Admin credits status retrieved!")
            print(f"Credits: {data['credits']}")
            print(f"Monthly credits: {data['monthly_credits']}")
            print(f"Yearly credits: {data['yearly_credits']}")
            
            if data['credits'] == 999999:
                print("Admin has unlimited credits!")
            else:
                print("Admin credits not set to unlimited")
        else:
            print(f"Failed to get credits: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error testing admin credits: {e}")

def test_admin_subscription(token):
    """Test admin user subscription status"""
    print("\nTesting admin user subscription...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            "http://localhost:8000/api/subscription/status",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print("Admin subscription status retrieved!")
            print(f"Subscription tier: {data['subscription_tier']}")
            print(f"Credits: {data['credits']}")
            
            if data['credits'] == 999999:
                print("Admin subscription shows unlimited credits!")
            else:
                print("Admin subscription credits not unlimited")
        else:
            print(f"Failed to get subscription: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error testing admin subscription: {e}")

def main():
    """Test admin functionality"""
    print("Testing Admin User Functionality")
    print("=" * 50)
    
    # Test admin login
    token = test_admin_login()
    if not token:
        print("Cannot proceed without valid admin token")
        return
    
    # Test admin credits
    test_admin_credits(token)
    
    # Test admin subscription
    test_admin_subscription(token)
    
    print("\n" + "=" * 50)
    print("Admin testing completed!")
    print("\nAdmin user details:")
    print("Email: admin@sorawatermarks.com")
    print("Password: admin123")
    print("Status: Unlimited credits, no restrictions")

if __name__ == "__main__":
    main()
