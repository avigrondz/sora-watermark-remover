#!/usr/bin/env python3
"""
Check if there are any videos in the database and their status.
"""

import sqlite3
import os

def check_videos():
    """Check videos in database"""
    db_path = "local_test.db"
    
    if not os.path.exists(db_path):
        print("Database file not found.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if jobs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
        if not cursor.fetchone():
            print("Jobs table not found")
            return
        
        # Get all jobs
        cursor.execute("SELECT id, status, original_file_path, processed_file_path FROM jobs ORDER BY id DESC LIMIT 10")
        jobs = cursor.fetchall()
        
        print(f"Found {len(jobs)} jobs:")
        for job in jobs:
            job_id, status, original_path, processed_path = job
            print(f"Job {job_id}: Status={status}, Original={original_path}, Processed={processed_path}")
            
            # Check if files exist
            if original_path and os.path.exists(original_path):
                print(f"  + Original file exists: {original_path}")
            else:
                print(f"  - Original file missing: {original_path}")
                
            if processed_path and os.path.exists(processed_path):
                print(f"  + Processed file exists: {processed_path}")
            else:
                print(f"  - Processed file missing: {processed_path}")
        
        # Check local storage directory
        local_storage = "local_storage"
        if os.path.exists(local_storage):
            print(f"\nLocal storage directory exists: {local_storage}")
            for root, dirs, files in os.walk(local_storage):
                for file in files:
                    if file.endswith(('.mp4', '.avi', '.mov')):
                        file_path = os.path.join(root, file)
                        print(f"  Video file: {file_path}")
        else:
            print(f"Local storage directory not found: {local_storage}")
            
    except Exception as e:
        print(f"Error checking videos: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_videos()
