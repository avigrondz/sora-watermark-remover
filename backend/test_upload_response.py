"""
Test Upload Response
"""

import requests
import tempfile
import os

def test_upload_response():
    """Test upload response format"""
    
    print("Testing Upload Response")
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
    
    # Step 2: Upload test file
    print("\n2. Uploading test file...")
    try:
        # Create a small test file
        test_content = b"test video content for upload test"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        with open(temp_file_path, "rb") as f:
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
        os.unlink(temp_file_path)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Response Data: {response_data}")
            
            if 'job_id' in response_data:
                print(f"+ Job ID found: {response_data['job_id']}")
                return True
            else:
                print("X No job_id in response")
                return False
        else:
            print(f"X Upload failed: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"X Upload error: {e}")
        return False

if __name__ == "__main__":
    if test_upload_response():
        print("\nUpload response is correct!")
    else:
        print("\nUpload response has issues")
