"""
Local Storage Service for Development
Fallback when S3 is not available
"""

import os
import shutil
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class LocalStorageService:
    def __init__(self):
        self.storage_dir = os.path.join(os.getcwd(), "local_storage")
        self.uploads_dir = os.path.join(self.storage_dir, "uploads")
        self.free_dir = os.path.join(self.uploads_dir, "free")
        self.paid_dir = os.path.join(self.uploads_dir, "paid")
        self.failed_dir = os.path.join(self.uploads_dir, "failed")
        
        # Create directories
        os.makedirs(self.free_dir, exist_ok=True)
        os.makedirs(self.paid_dir, exist_ok=True)
        os.makedirs(self.failed_dir, exist_ok=True)
    
    def upload_file(self, file_path: str, s3_key: str) -> bool:
        """Upload file to local storage"""
        try:
            # Determine target directory based on key
            if s3_key.startswith("uploads/free/"):
                target_dir = self.free_dir
            elif s3_key.startswith("uploads/paid/"):
                target_dir = self.paid_dir
            elif s3_key.startswith("uploads/failed/"):
                target_dir = self.failed_dir
            else:
                target_dir = self.uploads_dir
            
            # Create user directory
            user_id = s3_key.split("/")[2] if len(s3_key.split("/")) > 2 else "unknown"
            user_dir = os.path.join(target_dir, user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            # Copy file
            filename = os.path.basename(s3_key)
            target_path = os.path.join(user_dir, filename)
            shutil.copy2(file_path, target_path)
            
            logger.info(f"File stored locally: {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing file locally: {str(e)}")
            return False
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """Download file from local storage"""
        try:
            # Find file in storage
            for root, dirs, files in os.walk(self.storage_dir):
                for file in files:
                    if file in s3_key:
                        source_path = os.path.join(root, file)
                        shutil.copy2(source_path, local_path)
                        logger.info(f"File downloaded locally: {local_path}")
                        return True
            
            logger.error(f"File not found: {s3_key}")
            return False
            
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return False
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """Generate local file URL"""
        try:
            # Find file in storage
            for root, dirs, files in os.walk(self.storage_dir):
                for file in files:
                    if file in s3_key:
                        file_path = os.path.join(root, file)
                        # Return local file URL (for development)
                        return f"file://{os.path.abspath(file_path)}"
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating URL: {str(e)}")
            return None
    
    def delete_file(self, s3_key: str) -> bool:
        """Delete file from local storage"""
        try:
            # Find and delete file
            for root, dirs, files in os.walk(self.storage_dir):
                for file in files:
                    if file in s3_key:
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                        logger.info(f"File deleted locally: {file_path}")
                        return True
            
            logger.warning(f"File not found for deletion: {s3_key}")
            return True  # Consider it deleted if not found
            
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
    
    def get_file_url(self, s3_key: str) -> str:
        """Get local file URL"""
        # Find file and return local path
        for root, dirs, files in os.walk(self.storage_dir):
            for file in files:
                if file in s3_key:
                    return os.path.join(root, file)
        
        return s3_key  # Fallback to key
    
    def cleanup_expired_files(self):
        """Clean up expired files based on retention policy"""
        try:
            current_time = datetime.now()
            cleanup_count = 0
            
            # Clean up free trial files (7 days)
            for root, dirs, files in os.walk(self.free_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if current_time - file_time > timedelta(days=7):
                        os.remove(file_path)
                        cleanup_count += 1
            
            # Clean up paid user original files (30 days)
            for root, dirs, files in os.walk(self.paid_dir):
                for file in files:
                    if "original" in file or not "processed" in file:
                        file_path = os.path.join(root, file)
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if current_time - file_time > timedelta(days=30):
                            os.remove(file_path)
                            cleanup_count += 1
            
            # Clean up failed jobs (1 day)
            for root, dirs, files in os.walk(self.failed_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if current_time - file_time > timedelta(days=1):
                        os.remove(file_path)
                        cleanup_count += 1
            
            logger.info(f"Cleaned up {cleanup_count} expired files")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return 0

# Global instance
local_storage = LocalStorageService()
