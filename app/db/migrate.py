import sqlite3
import os
from pathlib import Path

def migrate_database():
    """
    Add the firebase_uid column to the user table if it doesn't exist
    """
    # Get the database path
    db_path = Path(__file__).parent.parent.parent / "db.sqlite"
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    print(f"Migrating database at {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the firebase_uid column exists in the user table
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    if "firebase_uid" not in column_names:
        print("Adding firebase_uid column to user table")
        # Add the firebase_uid column
        cursor.execute("ALTER TABLE user ADD COLUMN firebase_uid TEXT UNIQUE")
        conn.commit()
        print("Column added successfully")
    else:
        print("firebase_uid column already exists")
    
    # Close the connection
    conn.close()
    
    print("Migration completed")

if __name__ == "__main__":
    migrate_database()
