"""
Test Video Streaming Endpoint
This script tests that the streaming endpoint works without authentication
"""

import os
import sys
import requests
import json
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_streaming_without_auth():
    """Test streaming endpoint without authentication"""
    
    # First, get a job ID from the database
    try:
        # Login to get a job ID
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
            print("❌ Login failed - cannot get job ID")
            return False
        
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get jobs
        response = requests.get(
            "http://localhost:8000/api/jobs",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print("❌ Failed to get jobs")
            return False
        
        jobs = response.json()
        if not jobs:
            print("⚠️  No jobs found. Upload a video first.")
            return False
        
        # Find a completed job
        completed_job = None
        for job in jobs:
            if job.get("status") == "completed":
                completed_job = job
                break
        
        if not completed_job:
            print("⚠️  No completed jobs found.")
            return False
        
        job_id = completed_job.get("id")
        print(f"✅ Found completed job ID: {job_id}")
        
    except Exception as e:
        print(f"❌ Error getting job ID: {e}")
        return False
    
    # Test streaming without authentication
    try:
        print(f"\n🔍 Testing streaming endpoint without authentication...")
        response = requests.get(
            f"http://localhost:8000/api/videos/{job_id}/stream",
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Streaming endpoint works without authentication!")
            print(f"📁 Content-Type: {response.headers.get('content-type')}")
            print(f"📊 Content-Length: {response.headers.get('content-length')}")
            return True
        elif response.status_code == 403:
            print("❌ Streaming endpoint requires authentication")
            print("💡 The endpoint is still protected")
            return False
        else:
            print(f"❌ Streaming failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Streaming error: {e}")
        return False

def test_download_flow():
    """Test the complete download flow"""
    
    try:
        # Login
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
            print("❌ Login failed")
            return False
        
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get jobs
        response = requests.get(
            "http://localhost:8000/api/jobs",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print("❌ Failed to get jobs")
            return False
        
        jobs = response.json()
        if not jobs:
            print("⚠️  No jobs found")
            return False
        
        # Find a completed job
        completed_job = None
        for job in jobs:
            if job.get("status") == "completed":
                completed_job = job
                break
        
        if not completed_job:
            print("⚠️  No completed jobs found")
            return False
        
        job_id = completed_job.get("id")
        
        # Test download URL generation
        response = requests.get(
            f"http://localhost:8000/api/jobs/{job_id}/download",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            download_url = data.get("download_url")
            print(f"📥 Download URL: {download_url}")
            
            # Test the download URL
            if "localhost" in download_url:
                print("✅ Download URL points to localhost")
                
                # Test accessing the download URL
                response = requests.get(download_url, timeout=10)
                if response.status_code == 200:
                    print("✅ Download URL is accessible!")
                    return True
                else:
                    print(f"❌ Download URL not accessible: {response.status_code}")
                    return False
            else:
                print(f"❌ Download URL doesn't point to localhost: {download_url}")
                return False
        else:
            print(f"❌ Download URL generation failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Download flow error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Sora Watermark Remover - Streaming Test")
    print("=" * 50)
    
    # Test streaming without authentication
    print("1️⃣ Testing streaming without authentication...")
    if test_streaming_without_auth():
        print("✅ Streaming works without authentication")
    else:
        print("❌ Streaming still requires authentication")
    
    # Test complete download flow
    print("\n2️⃣ Testing complete download flow...")
    if test_download_flow():
        print("✅ Download flow is working!")
    else:
        print("❌ Download flow has issues")
