"""
Smart Storage Manager for Sora Watermark Remover
Handles file lifecycle, cleanup, and cost optimization
"""

import os
import boto3
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict
import logging
from app.models import User, Job, JobStatus, SubscriptionTier
from app.database import get_db

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        
        # Storage policies
        self.retention_policies = {
            'free_trial': {
                'original_video': 7,  # days
                'processed_video': 7,  # days
                'max_storage_gb': 1  # 1GB limit for free users
            },
            'paid_user': {
                'original_video': 30,  # days
                'processed_video': 90,  # days
                'max_storage_gb': 50  # 50GB limit for paid users
            },
            'failed_job': {
                'original_video': 1,  # 1 day for failed jobs
                'processed_video': 0,  # immediate deletion
                'max_storage_gb': 0.1  # minimal storage
            }
        }
    
    def get_user_storage_policy(self, user: User) -> Dict:
        """Get storage policy based on user subscription"""
        if user.subscription_tier == SubscriptionTier.FREE:
            return self.retention_policies['free_trial']
        else:
            return self.retention_policies['paid_user']
    
    def should_cleanup_file(self, job: Job, user: User) -> bool:
        """Check if a file should be cleaned up based on retention policy"""
        policy = self.get_user_storage_policy(user)
        
        # Different cleanup rules for different file types
        if job.status == JobStatus.FAILED:
            # Failed jobs get immediate cleanup
            return datetime.utcnow() - job.created_at > timedelta(days=1)
        
        # Check original video retention
        if job.original_file_path:
            original_age = datetime.utcnow() - job.created_at
            if original_age > timedelta(days=policy['original_video']):
                return True
        
        # Check processed video retention
        if job.processed_file_path and job.status == JobStatus.COMPLETED:
            if job.processing_completed_at:
                processed_age = datetime.utcnow() - job.processing_completed_at
                if processed_age > timedelta(days=policy['processed_video']):
                    return True
        
        return False
    
    def cleanup_expired_files(self, db: Session) -> Dict[str, int]:
        """Clean up expired files and return cleanup stats"""
        cleanup_stats = {
            'files_deleted': 0,
            'storage_freed_gb': 0,
            'errors': 0
        }
        
        try:
            # Get all jobs that might need cleanup
            jobs = db.query(Job).join(User).all()
            
            for job in jobs:
                if self.should_cleanup_file(job, job.user):
                    try:
                        # Delete original file
                        if job.original_file_path:
                            self._delete_s3_file(job.original_file_path)
                            job.original_file_path = None
                            cleanup_stats['files_deleted'] += 1
                        
                        # Delete processed file
                        if job.processed_file_path:
                            self._delete_s3_file(job.processed_file_path)
                            job.processed_file_path = None
                            cleanup_stats['files_deleted'] += 1
                        
                        # Update job record
                        db.commit()
                        
                    except Exception as e:
                        logger.error(f"Error cleaning up job {job.id}: {str(e)}")
                        cleanup_stats['errors'] += 1
            
            # Calculate storage freed (approximate)
            cleanup_stats['storage_freed_gb'] = cleanup_stats['files_deleted'] * 0.1  # Estimate
            
        except Exception as e:
            logger.error(f"Error in cleanup process: {str(e)}")
            cleanup_stats['errors'] += 1
        
        return cleanup_stats
    
    def _delete_s3_file(self, s3_key: str) -> bool:
        """Delete a file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted S3 file: {s3_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete S3 file {s3_key}: {str(e)}")
            return False
    
    def get_user_storage_usage(self, user_id: int, db: Session) -> Dict:
        """Get storage usage for a specific user"""
        try:
            # Get all user's jobs
            jobs = db.query(Job).filter(Job.user_id == user_id).all()
            
            total_size_bytes = 0
            file_count = 0
            
            for job in jobs:
                # Estimate file sizes (you could store actual sizes in the database)
                if job.original_file_path:
                    total_size_bytes += 100 * 1024 * 1024  # Estimate 100MB per video
                    file_count += 1
                
                if job.processed_file_path:
                    total_size_bytes += 100 * 1024 * 1024  # Estimate 100MB per processed video
                    file_count += 1
            
            return {
                'total_size_gb': round(total_size_bytes / (1024**3), 2),
                'file_count': file_count,
                'user_id': user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting storage usage for user {user_id}: {str(e)}")
            return {'total_size_gb': 0, 'file_count': 0, 'user_id': user_id}
    
    def check_storage_limits(self, user: User, db: Session) -> Dict:
        """Check if user is within storage limits"""
        usage = self.get_user_storage_usage(user.id, db)
        policy = self.get_user_storage_policy(user)
        
        return {
            'current_usage_gb': usage['total_size_gb'],
            'limit_gb': policy['max_storage_gb'],
            'within_limit': usage['total_size_gb'] < policy['max_storage_gb'],
            'usage_percentage': (usage['total_size_gb'] / policy['max_storage_gb']) * 100
        }
    
    def setup_s3_lifecycle_policy(self):
        """Set up S3 lifecycle policies for automatic cleanup"""
        lifecycle_policy = {
            'Rules': [
                {
                    'ID': 'FreeTrialCleanup',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'uploads/free/'},
                    'Expiration': {'Days': 7}
                },
                {
                    'ID': 'PaidUserOriginalCleanup',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'uploads/paid/original/'},
                    'Expiration': {'Days': 30}
                },
                {
                    'ID': 'PaidUserProcessedCleanup',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'uploads/paid/processed/'},
                    'Expiration': {'Days': 90}
                },
                {
                    'ID': 'FailedJobsCleanup',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'uploads/failed/'},
                    'Expiration': {'Days': 1}
                }
            ]
        }
        
        try:
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=lifecycle_policy
            )
            logger.info("S3 lifecycle policy configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure S3 lifecycle policy: {str(e)}")

# Global instance
storage_manager = StorageManager()
