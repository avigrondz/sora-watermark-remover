"""
Check Server Status
"""

import socket
import requests
import time

def check_server():
    """Check if server is accessible"""
    
    print("Checking Server Status")
    print("=" * 30)
    
    # Test 1: Port check
    print("\n1. Checking port 8000...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result == 0:
            print("+ Port 8000 is open")
        else:
            print("X Port 8000 is closed")
            return False
    except Exception as e:
        print(f"X Port check error: {e}")
        return False
    
    # Test 2: HTTP check with different timeout
    print("\n2. Testing HTTP connection...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=2)
        if response.status_code == 200:
            print("+ HTTP connection working")
        else:
            print(f"X HTTP returned: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("X HTTP timeout - server might be hanging")
        return False
    except Exception as e:
        print(f"X HTTP error: {e}")
        return False
    
    print("\n+ Server is accessible!")
    return True

if __name__ == "__main__":
    if check_server():
        print("\nServer is working!")
    else:
        print("\nServer has issues")
