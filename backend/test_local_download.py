"""
Test Local Download URLs
This script tests that download URLs point to localhost instead of S3
"""

import os
import sys
import requests
import json
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_download_urls():
    """Test that download URLs are localhost URLs, not S3 URLs"""
    
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
            print(f"📥 Download URL: {download_url}")
            
            # Check if URL is localhost (good) or S3 (bad)
            if "localhost" in download_url or "127.0.0.1" in download_url:
                print("✅ Download URL points to localhost - GOOD!")
                return True
            elif "s3.amazonaws.com" in download_url:
                print("❌ Download URL points to S3 - BAD!")
                print("💡 This means the file is not being found in local storage")
                return False
            else:
                print(f"⚠️  Unknown URL format: {download_url}")
                return False
        else:
            print(f"❌ Download URL generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Download URL error: {e}")
        return False

def check_file_locations():
    """Check where files are actually stored"""
    
    print("\n📁 Checking file locations...")
    
    storage_dir = "local_storage"
    if not os.path.exists(storage_dir):
        print("❌ Local storage directory not found")
        return False
    
    print(f"✅ Local storage directory exists: {storage_dir}")
    
    # Find all video files
    video_files = []
    for root, dirs, files in os.walk(storage_dir):
        for file in files:
            if file.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                video_files.append((file_path, file_size))
    
    if video_files:
        print(f"✅ Found {len(video_files)} video files:")
        for file_path, file_size in video_files:
            print(f"  📹 {file_path} ({file_size} bytes)")
    else:
        print("⚠️  No video files found in local storage")
    
    return len(video_files) > 0

if __name__ == "__main__":
    print("🧪 Sora Watermark Remover - Local Download Test")
    print("=" * 60)
    
    # Check file locations
    if not check_file_locations():
        print("❌ No files found in local storage")
        print("💡 Upload a video first")
        sys.exit(1)
    
    # Test download URLs
    print("\n🔍 Testing download URLs...")
    if test_download_urls():
        print("\n🎉 Download URLs are working correctly!")
        print("✅ URLs point to localhost instead of S3")
    else:
        print("\n❌ Download URLs have issues")
        print("💡 Check the server logs for file location details")
