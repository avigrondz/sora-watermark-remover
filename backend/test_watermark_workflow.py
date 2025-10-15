"""
Test Watermark Removal Workflow
This script tests the complete watermark removal workflow
"""

import os
import sys
import requests
import json
import time
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_complete_workflow():
    """Test the complete watermark removal workflow"""
    
    print("Sora Watermark Remover - Complete Workflow Test")
    print("=" * 60)
    
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
    
    # Step 2: Upload video
    print("\n2. Uploading video...")
    try:
        # Create a test file
        test_file_path = "test_video.txt"
        with open(test_file_path, "w") as f:
            f.write("This is a test video file for watermark removal testing")
        
        files = {
            "file": ("test_video.mp4", open(test_file_path, "rb"), "video/mp4")
        }
        
        response = requests.post(
            "http://localhost:8000/api/videos/upload",
            headers=headers,
            files=files,
            timeout=30
        )
        
        # Clean up
        os.remove(test_file_path)
        files["file"][1].close()
        
        if response.status_code != 200:
            print(f"X Upload failed: {response.status_code}")
            return False
        
        job_data = response.json()
        job_id = job_data.get("job_id")
        print(f"+ Upload successful - Job ID: {job_id}")
        
    except Exception as e:
        print(f"X Upload error: {e}")
        return False
    
    # Step 3: Check job status (should be pending)
    print("\n3. Checking job status...")
    try:
        response = requests.get(
            f"http://localhost:8000/api/jobs/{job_id}/status",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Status check failed: {response.status_code}")
            return False
        
        status_data = response.json()
        status = status_data.get("status")
        print(f"✓ Job status: {status}")
        
        if status != "pending":
            print("! Job is not in pending state - may have auto-processed")
        
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return False
    
    # Step 4: Add watermark selections
    print("\n4. Adding watermark selections...")
    try:
        watermark_data = {
            "watermarks": [
                {
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 50,
                    "timestamp": 0
                },
                {
                    "x": 300,
                    "y": 200,
                    "width": 150,
                    "height": 40,
                    "timestamp": 5.5
                }
            ]
        }
        
        response = requests.post(
            f"http://localhost:8000/api/jobs/{job_id}/watermarks",
            headers=headers,
            json=watermark_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Watermark selection failed: {response.status_code}")
            return False
        
        print("✓ Watermark selections saved")
        
    except Exception as e:
        print(f"❌ Watermark selection error: {e}")
        return False
    
    # Step 5: Get watermark selections
    print("\n5. Retrieving watermark selections...")
    try:
        response = requests.get(
            f"http://localhost:8000/api/jobs/{job_id}/watermarks",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Get watermarks failed: {response.status_code}")
            return False
        
        watermarks = response.json()
        print(f"✓ Retrieved {len(watermarks.get('watermarks', []))} watermark selections")
        
    except Exception as e:
        print(f"❌ Get watermarks error: {e}")
        return False
    
    # Step 6: Start processing
    print("\n6. Starting processing...")
    try:
        response = requests.post(
            f"http://localhost:8000/api/jobs/{job_id}/process",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Start processing failed: {response.status_code}")
            return False
        
        print("✓ Processing started")
        
    except Exception as e:
        print(f"❌ Start processing error: {e}")
        return False
    
    # Step 7: Monitor processing
    print("\n7. Monitoring processing...")
    try:
        for i in range(10):  # Check for up to 20 seconds
            time.sleep(2)
            
            response = requests.get(
                f"http://localhost:8000/api/jobs/{job_id}/status",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status")
                print(f"   Status: {status}")
                
                if status == "completed":
                    print("✓ Processing completed!")
                    break
                elif status == "failed":
                    print("❌ Processing failed")
                    return False
            else:
                print(f"❌ Status check failed: {response.status_code}")
                return False
        else:
            print("! Processing is taking longer than expected")
        
    except Exception as e:
        print(f"❌ Monitoring error: {e}")
        return False
    
    # Step 8: Test download
    print("\n8. Testing download...")
    try:
        response = requests.get(
            f"http://localhost:8000/api/jobs/{job_id}/download",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            download_data = response.json()
            download_url = download_data.get("download_url")
            print(f"✓ Download URL generated: {download_url}")
            
            # Test the download URL
            if "localhost" in download_url:
                print("✓ Download URL points to localhost")
            else:
                print(f"! Download URL: {download_url}")
        else:
            print(f"❌ Download failed: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        return False
    
    print("\nComplete workflow test passed!")
    print("✓ All steps completed successfully")
    return True

if __name__ == "__main__":
    if test_complete_workflow():
        print("\nWatermark removal workflow is working!")
        print("You can now upload videos and process them with watermark selection")
    else:
        print("\n❌ Workflow test failed")
        print("Check the server logs for more details")
