#!/usr/bin/env python3
"""
Create a test video for job 62 to test video streaming.
"""

import os
import sqlite3

def create_test_video():
    """Create a test video file for job 62"""
    
    # Create the directory structure
    os.makedirs("local_storage/uploads/free/3", exist_ok=True)
    
    # Create a simple test video file (just a text file for now)
    test_video_path = "local_storage/uploads/free/3/30804f17-f8da-48ff-a859-9aa6cf07c573.mp4"
    
    # Create a simple test file
    with open(test_video_path, 'w') as f:
        f.write("This is a test video file for job 62")
    
    print(f"Created test video: {test_video_path}")
    
    # Update the database to point to the correct path
    db_path = "local_test.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE jobs SET original_file_path = ? WHERE id = 62", (test_video_path,))
        conn.commit()
        print("Updated database path for job 62")
    except Exception as e:
        print(f"Error updating database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_test_video()
