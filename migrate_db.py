#!/usr/bin/env python3
"""
Flask-based migration runner using existing app configuration
"""
from app import create_app
from app.database import db
from sqlalchemy import text

def run_migration():
    app = create_app()
    
    with app.app_context():
        try:
            print("Running database migration...")
            
            # Fix audit_logs table structure
            migrations = [
                "ALTER TABLE audit_logs MODIFY COLUMN previous_value LONGTEXT",
                "ALTER TABLE audit_logs MODIFY COLUMN new_value LONGTEXT", 
                "ALTER TABLE audit_logs MODIFY COLUMN notes LONGTEXT"
            ]
            
            # Add last_audit_time column if it doesn't exist
            try:
                db.engine.execute(text("ALTER TABLE products ADD COLUMN last_audit_time DATETIME NULL"))
                print("✓ Added last_audit_time column to products table")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("⚠ last_audit_time column already exists")
                else:
                    print(f"✗ Error adding last_audit_time: {e}")
            
            for migration in migrations:
                try:
                    db.engine.execute(text(migration))
                    print(f"✓ Executed: {migration}")
                except Exception as e:
                    print(f"✗ Error: {migration} - {e}")
            
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    run_migration()