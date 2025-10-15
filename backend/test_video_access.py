"""
Test Video Access for Watermark Selection
"""

import requests
import json

def test_video_access():
    """Test video access for watermark selection"""
    
    print("Testing Video Access")
    print("=" * 30)
    
    # Step 1: Login
    print("\n1. Logging in...")
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
        
        if response.status_code != 200:
            print("X Login failed")
            return False
        
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("+ Login successful")
        
    except Exception as e:
        print(f"X Login error: {e}")
        return False
    
    # Step 2: Get latest job
    print("\n2. Getting latest job...")
    try:
        response = requests.get(
            "http://localhost:8000/api/jobs",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"X Jobs failed: {response.status_code}")
            return False
        
        jobs = response.json()
        print(f"+ Found {len(jobs)} jobs")
        
        if not jobs:
            print("X No jobs found")
            return False
        
        # Get the latest job
        latest_job = jobs[0]
        job_id = latest_job.get('id')
        print(f"+ Latest job ID: {job_id}")
        print(f"+ Job status: {latest_job.get('status')}")
        print(f"+ Original file path: {latest_job.get('original_file_path')}")
        print(f"+ Processed file path: {latest_job.get('processed_file_path')}")
        
    except Exception as e:
        print(f"X Jobs error: {e}")
        return False
    
    # Step 3: Test video stream
    print("\n3. Testing video stream...")
    try:
        stream_url = f"http://localhost:8000/api/videos/{job_id}/stream"
        print(f"Stream URL: {stream_url}")
        
        # Test with GET request
        response = requests.get(stream_url, timeout=10)
        print(f"GET Response: {response.status_code}")
        
        if response.status_code == 200:
            print("+ Video stream accessible")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content-Length: {response.headers.get('content-length')}")
        else:
            print(f"X Video stream failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"X Video stream error: {e}")
        return False
    
    print("\n+ Video access test completed!")
    return True

if __name__ == "__main__":
    if test_video_access():
        print("\nVideo access is working!")
        print("The watermark selection tool should work now.")
    else:
        print("\nVideo access has issues")
        print("Check the server logs for more details.")
