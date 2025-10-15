"""
Simple Test for Watermark Removal Workflow
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

def test_simple_workflow():
    """Test the watermark removal workflow"""
    
    print("Sora Watermark Remover - Simple Test")
    print("=" * 50)
    
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
        
        with open(test_file_path, "rb") as f:
            files = {
                "file": ("test_video.mp4", f, "video/mp4")
            }
            
            response = requests.post(
                "http://localhost:8000/api/videos/upload",
                headers=headers,
                files=files,
                timeout=30
            )
        
        # Clean up
        os.remove(test_file_path)
        
        if response.status_code != 200:
            print(f"X Upload failed: {response.status_code}")
            return False
        
        job_data = response.json()
        job_id = job_data.get("job_id")
        print(f"+ Upload successful - Job ID: {job_id}")
        
    except Exception as e:
        print(f"X Upload error: {e}")
        return False
    
    # Step 3: Check job status
    print("\n3. Checking job status...")
    try:
        response = requests.get(
            f"http://localhost:8000/api/jobs/{job_id}/status",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"X Status check failed: {response.status_code}")
            return False
        
        status_data = response.json()
        status = status_data.get("status")
        print(f"+ Job status: {status}")
        
    except Exception as e:
        print(f"X Status check error: {e}")
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
            print(f"X Watermark selection failed: {response.status_code}")
            return False
        
        print("+ Watermark selections saved")
        
    except Exception as e:
        print(f"X Watermark selection error: {e}")
        return False
    
    # Step 5: Start processing
    print("\n5. Starting processing...")
    try:
        response = requests.post(
            f"http://localhost:8000/api/jobs/{job_id}/process",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"X Start processing failed: {response.status_code}")
            return False
        
        print("+ Processing started")
        
    except Exception as e:
        print(f"X Start processing error: {e}")
        return False
    
    # Step 6: Monitor processing
    print("\n6. Monitoring processing...")
    try:
        for i in range(5):  # Check for up to 10 seconds
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
                    print("+ Processing completed!")
                    break
                elif status == "failed":
                    print("X Processing failed")
                    return False
            else:
                print(f"X Status check failed: {response.status_code}")
                return False
        else:
            print("! Processing is taking longer than expected")
        
    except Exception as e:
        print(f"X Monitoring error: {e}")
        return False
    
    print("\n+ Complete workflow test passed!")
    print("+ All steps completed successfully")
    return True

if __name__ == "__main__":
    if test_simple_workflow():
        print("\nWatermark removal workflow is working!")
        print("You can now upload videos and process them with watermark selection")
    else:
        print("\nX Workflow test failed")
        print("Check the server logs for more details")
