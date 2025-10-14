"""
Cleanup tasks for storage management
"""

from celery import Celery
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Job, JobStatus, SubscriptionTier
from services.storage_manager import storage_manager
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Initialize Celery app (you'll need to configure this)
celery_app = Celery('cleanup_tasks')

@celery_app.task
def cleanup_expired_files():
    """Daily cleanup task to remove expired files"""
    try:
        db = next(get_db())
        stats = storage_manager.cleanup_expired_files(db)
        
        logger.info(f"Cleanup completed: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        return {'error': str(e)}
    finally:
        db.close()

@celery_app.task
def check_user_storage_limits():
    """Check storage limits for all users and notify if needed"""
    try:
        db = next(get_db())
        
        # Get all users
        users = db.query(User).all()
        
        for user in users:
            limits = storage_manager.check_storage_limits(user, db)
            
            if not limits['within_limit']:
                logger.warning(f"User {user.id} exceeded storage limit: {limits}")
                # You could send an email notification here
                
        return {'checked_users': len(users)}
        
    except Exception as e:
        logger.error(f"Storage limit check failed: {str(e)}")
        return {'error': str(e)}
    finally:
        db.close()

@celery_app.task
def cleanup_failed_jobs():
    """Clean up failed jobs older than 24 hours"""
    try:
        db = next(get_db())
        
        # Find failed jobs older than 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        failed_jobs = db.query(Job).filter(
            Job.status == JobStatus.FAILED,
            Job.created_at < cutoff_time
        ).all()
        
        deleted_count = 0
        for job in failed_jobs:
            try:
                # Delete files
                if job.original_file_path:
                    storage_manager._delete_s3_file(job.original_file_path)
                
                # Delete job record
                db.delete(job)
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Failed to delete job {job.id}: {str(e)}")
        
        db.commit()
        logger.info(f"Cleaned up {deleted_count} failed jobs")
        return {'deleted_jobs': deleted_count}
        
    except Exception as e:
        logger.error(f"Failed jobs cleanup failed: {str(e)}")
        return {'error': str(e)}
    finally:
        db.close()

# Schedule these tasks
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run cleanup every day at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        cleanup_expired_files.s(),
        name='daily-cleanup'
    )
    
    # Check storage limits every 6 hours
    sender.add_periodic_task(
        crontab(hour='*/6', minute=0),
        check_user_storage_limits.s(),
        name='storage-limit-check'
    )
    
    # Clean up failed jobs every hour
    sender.add_periodic_task(
        crontab(minute=0),
        cleanup_failed_jobs.s(),
        name='failed-jobs-cleanup'
    )
