#!/usr/bin/env python3
"""
Fix video file paths in database to point to correct local_storage files.
"""

import sqlite3
import os
import glob

def fix_video_paths():
    """Fix video file paths in database"""
    db_path = "local_test.db"
    
    if not os.path.exists(db_path):
        print("Database file not found.")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all jobs with missing original files
        cursor.execute("SELECT id, original_file_path, processed_file_path FROM jobs WHERE original_file_path IS NOT NULL")
        jobs = cursor.fetchall()
        
        print(f"Found {len(jobs)} jobs to check:")
        
        for job_id, original_path, processed_path in jobs:
            print(f"\nJob {job_id}:")
            print(f"  Original: {original_path}")
            print(f"  Processed: {processed_path}")
            
            # Check if original file exists
            if original_path and not os.path.exists(original_path):
                print(f"  - Original file missing: {original_path}")
                
                # Look for the file in local_storage
                filename = os.path.basename(original_path)
                search_pattern = f"local_storage/**/{filename}"
                found_files = glob.glob(search_pattern, recursive=True)
                
                if found_files:
                    new_path = found_files[0]
                    print(f"  + Found in local_storage: {new_path}")
                    
                    # Update the database
                    cursor.execute("UPDATE jobs SET original_file_path = ? WHERE id = ?", (new_path, job_id))
                    print(f"  + Updated database path")
                else:
                    print(f"  - File not found in local_storage")
            else:
                print(f"  + Original file exists")
            
            # Check if processed file exists
            if processed_path and not os.path.exists(processed_path):
                print(f"  - Processed file missing: {processed_path}")
                
                # Look for the file in local_storage
                filename = os.path.basename(processed_path)
                search_pattern = f"local_storage/**/{filename}"
                found_files = glob.glob(search_pattern, recursive=True)
                
                if found_files:
                    new_path = found_files[0]
                    print(f"  + Found in local_storage: {new_path}")
                    
                    # Update the database
                    cursor.execute("UPDATE jobs SET processed_file_path = ? WHERE id = ?", (new_path, job_id))
                    print(f"  + Updated database path")
                else:
                    print(f"  - File not found in local_storage")
            else:
                print(f"  + Processed file exists")
        
        conn.commit()
        print("\nDatabase paths updated successfully!")
        return True
        
    except Exception as e:
        print(f"Error fixing video paths: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Fix video file paths"""
    print("Fixing video file paths in database...")
    
    if fix_video_paths():
        print("Video paths fixed successfully!")
    else:
        print("Failed to fix video paths")

if __name__ == "__main__":
    main()
