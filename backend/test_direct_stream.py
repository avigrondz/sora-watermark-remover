"""
Test Direct Video Stream
"""

import requests

def test_direct_stream():
    """Test direct video stream access"""
    
    print("Testing Direct Video Stream")
    print("=" * 30)
    
    # Test the stream URL directly
    stream_url = "http://localhost:8000/api/videos/9/stream"
    print(f"Testing: {stream_url}")
    
    try:
        # Use GET request to check if endpoint exists
        response = requests.get(stream_url, timeout=10)
        print(f"GET Response: {response.status_code}")
        
        if response.status_code == 200:
            print("+ Video stream accessible")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content-Length: {response.headers.get('content-length')}")
        else:
            print(f"X Video stream failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"X Video stream error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_direct_stream()
