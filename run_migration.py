#!/usr/bin/env python3
"""
Simple migration runner to fix audit_logs table structure
"""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    connection = None
    try:
        # Database connection using the credentials from config
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='#Lerengesu',  # URL decoded password
            database='kibs_ims_db'
        )
        
        cursor = connection.cursor()
        
        print("Running database migration...")
        
        # Fix audit_logs table structure
        migrations = [
            "ALTER TABLE audit_logs MODIFY COLUMN previous_value LONGTEXT",
            "ALTER TABLE audit_logs MODIFY COLUMN new_value LONGTEXT", 
            "ALTER TABLE audit_logs MODIFY COLUMN notes LONGTEXT",
            "ALTER TABLE products ADD COLUMN last_audit_time DATETIME NULL"
        ]
        
        for migration in migrations:
            try:
                cursor.execute(migration)
                print(f"✓ Executed: {migration}")
            except mysql.connector.Error as e:
                if "Duplicate column name" in str(e):
                    print(f"⚠ Column already exists: {migration}")
                else:
                    print(f"✗ Error: {migration} - {e}")
        
        connection.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    run_migration()