"""
Quick fix for upload issues
This script will help you get uploads working immediately
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def fix_upload_issue():
    """Fix the upload issue by setting up local storage"""
    
    print("🔧 Fixing upload issue...")
    
    # Create local storage directory
    storage_dir = os.path.join(backend_dir, "local_storage")
    uploads_dir = os.path.join(storage_dir, "uploads")
    
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(os.path.join(uploads_dir, "free"), exist_ok=True)
    os.makedirs(os.path.join(uploads_dir, "paid"), exist_ok=True)
    os.makedirs(os.path.join(uploads_dir, "failed"), exist_ok=True)
    
    print(f"✅ Created local storage directory: {storage_dir}")
    
    # Check if S3 bucket exists
    try:
        from services.s3_service import s3_service
        s3_service.s3_client.head_bucket(Bucket=s3_service.bucket_name)
        print("✅ S3 bucket is accessible")
        return True
    except Exception as e:
        print(f"⚠️  S3 bucket not accessible: {e}")
        print("✅ Local storage fallback is ready")
        return False

def test_upload():
    """Test if uploads work now"""
    
    print("\n🧪 Testing upload functionality...")
    
    try:
        # Test local storage
        from services.local_storage import local_storage
        
        # Create a test file
        test_file = os.path.join(backend_dir, "test_upload.txt")
        with open(test_file, "w") as f:
            f.write("Test upload content")
        
        # Test upload
        success = local_storage.upload_file(test_file, "test/upload.txt")
        
        # Clean up
        os.remove(test_file)
        
        if success:
            print("✅ Local storage upload test successful")
            return True
        else:
            print("❌ Local storage upload test failed")
            return False
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Upload Fix Script")
    print("=" * 30)
    
    if fix_upload_issue():
        print("\n🎉 Upload should work now!")
        print("💡 Your uploads will be stored locally for development")
    else:
        print("\n✅ Local storage fallback is ready!")
        print("💡 Uploads will work with local storage")
    
    if test_upload():
        print("\n🎉 Upload functionality is working!")
    else:
        print("\n⚠️  There may still be issues with uploads")
    
    print("\n📝 Next steps:")
    print("1. Restart your server")
    print("2. Try uploading a video")
    print("3. Files will be stored in backend/local_storage/")
