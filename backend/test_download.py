"""
Test Download Functionality
This script tests the download and streaming endpoints
"""

import os
import sys
import requests
import json
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_download_endpoints():
    """Test download and streaming endpoints"""
    
    # Test login first
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
            print("❌ Login failed - cannot test downloads")
            return False
        
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        print("✅ Login successful")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Get user's jobs
    try:
        response = requests.get(
            "http://localhost:8000/api/jobs",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print("❌ Failed to get jobs")
            return False
        
        jobs = response.json()
        print(f"✅ Found {len(jobs)} jobs")
        
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
            print("⚠️  No completed jobs found. Upload and wait for processing.")
            return False
        
        job_id = completed_job.get("id")
        print(f"✅ Testing with job ID: {job_id}")
        
    except Exception as e:
        print(f"❌ Error getting jobs: {e}")
        return False
    
    # Test download URL generation
    try:
        response = requests.get(
            f"http://localhost:8000/api/jobs/{job_id}/download",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            download_url = data.get("download_url")
            print(f"✅ Download URL generated: {download_url}")
        else:
            print(f"❌ Download URL generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Download URL error: {e}")
        return False
    
    # Test video streaming
    try:
        response = requests.get(
            f"http://localhost:8000/api/videos/{job_id}/stream",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Video streaming endpoint working")
            print(f"📁 Content-Type: {response.headers.get('content-type')}")
            print(f"📊 Content-Length: {response.headers.get('content-length')}")
        else:
            print(f"❌ Video streaming failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Video streaming error: {e}")
        return False
    
    return True

def check_local_storage():
    """Check what files are in local storage"""
    
    print("\n📁 Checking local storage...")
    
    storage_dir = "local_storage"
    if not os.path.exists(storage_dir):
        print("❌ Local storage directory not found")
        return False
    
    print(f"✅ Local storage directory exists: {storage_dir}")
    
    # Walk through local storage
    for root, dirs, files in os.walk(storage_dir):
        level = root.replace(storage_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            print(f"{subindent}{file} ({file_size} bytes)")
    
    return True

if __name__ == "__main__":
    print("🧪 Sora Watermark Remover - Download Test")
    print("=" * 50)
    
    # Check local storage
    check_local_storage()
    
    # Test download endpoints
    print("\n🔍 Testing download functionality...")
    if test_download_endpoints():
        print("\n🎉 Download functionality is working!")
        print("✅ You can now download and view videos")
    else:
        print("\n❌ Download functionality has issues")
        print("💡 Check the server logs for more details")
