"""
Debug Server Status
"""

import requests
import time

def debug_server():
    """Debug server status"""
    
    print("Debugging Server Status")
    print("=" * 30)
    
    # Test 1: Basic connectivity
    print("\n1. Testing basic connectivity...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("+ Server is running")
        else:
            print(f"X Server returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"X Server not responding: {e}")
        return False
    
    # Test 2: Login
    print("\n2. Testing login...")
    try:
        login_data = {
            "email": "admin@sorawatermarks.com",
            "password": "admin123"
        }
        
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            json=login_data,
            timeout=5
        )
        
        if response.status_code == 200:
            print("+ Login working")
            token = response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
        else:
            print(f"X Login failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"X Login error: {e}")
        return False
    
    # Test 3: Simple endpoint
    print("\n3. Testing simple endpoint...")
    try:
        response = requests.get(
            "http://localhost:8000/api/auth/me",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            print("+ Auth endpoint working")
        else:
            print(f"X Auth endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"X Auth endpoint error: {e}")
        return False
    
    print("\n+ Server is working correctly!")
    return True

if __name__ == "__main__":
    if debug_server():
        print("\nServer is healthy!")
    else:
        print("\nServer has issues - may need restart")
