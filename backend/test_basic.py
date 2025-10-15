"""
Basic Test for Server Connectivity
"""

import requests
import json

def test_basic_connectivity():
    """Test basic server connectivity"""
    
    print("Basic Server Test")
    print("=" * 30)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("+ Health check passed")
        else:
            print(f"X Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"X Health check error: {e}")
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
            timeout=10
        )
        
        if response.status_code == 200:
            print("+ Login successful")
            token = response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
        else:
            print(f"X Login failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"X Login error: {e}")
        return False
    
    # Test 3: Get jobs
    print("\n3. Testing jobs endpoint...")
    try:
        response = requests.get(
            "http://localhost:8000/api/jobs",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            jobs = response.json()
            print(f"+ Jobs endpoint working - found {len(jobs)} jobs")
        else:
            print(f"X Jobs endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"X Jobs endpoint error: {e}")
        return False
    
    print("\n+ All basic tests passed!")
    return True

if __name__ == "__main__":
    if test_basic_connectivity():
        print("\nServer is working correctly!")
    else:
        print("\nServer has issues - check the logs")
