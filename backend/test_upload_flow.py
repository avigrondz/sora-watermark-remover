"""
Test Upload Flow Script
This script tests the complete upload flow to ensure everything works
"""

import os
import sys
import requests
import json
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_api_connection():
    """Test if the API is running"""
    
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Is the server running?")
        print("💡 Start the server with: python start_dev.py")
        return False
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False

def test_login():
    """Test admin login"""
    
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
            data = response.json()
            token = data.get("access_token")
            print("✅ Login successful")
            return token
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_upload(token):
    """Test file upload"""
    
    try:
        # Create a small test file
        test_file_path = "test_video.txt"
        with open(test_file_path, "w") as f:
            f.write("This is a test video file for upload testing")
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # Prepare file upload
        files = {
            "file": ("test_video.mp4", open(test_file_path, "rb"), "video/mp4")
        }
        
        response = requests.post(
            "http://localhost:8000/api/videos/upload",
            headers=headers,
            files=files,
            timeout=30
        )
        
        # Clean up test file
        os.remove(test_file_path)
        files["file"][1].close()
        
        if response.status_code == 200:
            data = response.json()
            job_id = data.get("job_id")
            print(f"✅ Upload successful - Job ID: {job_id}")
            return job_id
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def test_job_status(token, job_id):
    """Test job status check"""
    
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(
            f"http://localhost:8000/api/jobs/{job_id}/status",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            print(f"✅ Job status: {status}")
            return status
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return None

def test_download(token, job_id):
    """Test download functionality"""
    
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(
            f"http://localhost:8000/api/jobs/{job_id}/download",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            download_url = data.get("download_url")
            print(f"✅ Download URL generated: {download_url}")
            return download_url
        else:
            print(f"❌ Download failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Download error: {e}")
        return None

def test_video_stream(token, job_id):
    """Test video streaming"""
    
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(
            f"http://localhost:8000/api/videos/{job_id}/stream",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Video streaming endpoint working")
            return True
        else:
            print(f"❌ Video streaming failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Video streaming error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Sora Watermark Remover - Upload Flow Test")
    print("=" * 60)
    
    # Step 1: Test API connection
    print("\n1️⃣ Testing API connection...")
    if not test_api_connection():
        print("❌ Cannot proceed without API connection")
        sys.exit(1)
    
    # Step 2: Test login
    print("\n2️⃣ Testing admin login...")
    token = test_login()
    if not token:
        print("❌ Cannot proceed without authentication")
        sys.exit(1)
    
    # Step 3: Test upload
    print("\n3️⃣ Testing file upload...")
    job_id = test_upload(token)
    if not job_id:
        print("❌ Upload failed")
        sys.exit(1)
    
    # Step 4: Test job status
    print("\n4️⃣ Testing job status...")
    status = test_job_status(token, job_id)
    if not status:
        print("❌ Status check failed")
        sys.exit(1)
    
    # Step 5: Test download
    print("\n5️⃣ Testing download...")
    download_url = test_download(token, job_id)
    if not download_url:
        print("❌ Download failed")
        sys.exit(1)
    
    # Step 6: Test video streaming
    print("\n6️⃣ Testing video streaming...")
    if not test_video_stream(token, job_id):
        print("❌ Video streaming failed")
        sys.exit(1)
    
    print("\n🎉 All tests passed!")
    print("✅ Upload flow is working correctly")
    print("✅ Videos are stored in local_storage/")
    print("✅ You can now upload and view videos in the UI")
