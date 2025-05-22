from app import db
from sqlalchemy import Column, DateTime, Text, Boolean

def add_missing_columns():
    """Add missing columns to the users table"""
    
    # Connect to the database
    connection = db.engine.connect()
    
    # Check if last_activity column exists
    result = connection.execute("SHOW COLUMNS FROM users LIKE 'last_activity'")
    if not result.fetchone():
        print("Adding last_activity column to users table")
        connection.execute("ALTER TABLE users ADD COLUMN last_activity DATETIME NULL")
    
    # Check if reset_token column exists
    result = connection.execute("SHOW COLUMNS FROM users LIKE 'reset_token'")
    if not result.fetchone():
        print("Adding reset_token column to users table")
        connection.execute("ALTER TABLE users ADD COLUMN reset_token VARCHAR(128) NULL")
    
    # Check if permissions column exists
    result = connection.execute("SHOW COLUMNS FROM users LIKE 'permissions'")
    if not result.fetchone():
        print("Adding permissions column to users table")
        connection.execute("ALTER TABLE users ADD COLUMN permissions TEXT NULL")
    
    # Check if is_banned column exists
    result = connection.execute("SHOW COLUMNS FROM users LIKE 'is_banned'")
    if not result.fetchone():
        print("Adding is_banned column to users table")
        connection.execute("ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT FALSE")
    
    # Check if ban_reason column exists
    result = connection.execute("SHOW COLUMNS FROM users LIKE 'ban_reason'")
    if not result.fetchone():
        print("Adding ban_reason column to users table")
        connection.execute("ALTER TABLE users ADD COLUMN ban_reason TEXT NULL")
    
    connection.close()
    print("Database schema update complete")

if __name__ == "__main__":
    add_missing_columns()