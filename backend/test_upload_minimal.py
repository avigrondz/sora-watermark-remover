"""
Minimal Upload Test
"""

import requests
import tempfile
import os

def test_minimal_upload():
    """Test minimal upload functionality"""
    
    print("Minimal Upload Test")
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
    
    # Step 2: Create minimal test file
    print("\n2. Creating test file...")
    try:
        # Create a very small test file
        test_content = b"test video content"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        print(f"+ Test file created: {temp_file_path}")
        
    except Exception as e:
        print(f"X File creation error: {e}")
        return False
    
    # Step 3: Upload with minimal timeout
    print("\n3. Uploading file...")
    try:
        with open(temp_file_path, "rb") as f:
            files = {
                "file": ("test_video.mp4", f, "video/mp4")
            }
            
            response = requests.post(
                "http://localhost:8000/api/videos/upload",
                headers=headers,
                files=files,
                timeout=10  # Short timeout
            )
        
        # Clean up
        os.unlink(temp_file_path)
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data.get("job_id")
            print(f"+ Upload successful - Job ID: {job_id}")
            return True
        else:
            print(f"X Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"X Upload error: {e}")
        # Clean up
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        return False

if __name__ == "__main__":
    if test_minimal_upload():
        print("\n+ Upload test passed!")
    else:
        print("\nX Upload test failed")
