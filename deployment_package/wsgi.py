#!/usr/bin/env python3
"""
WSGI entry point for PythonAnywhere deployment
"""
import sys
import os

# Add your project directory to the Python path
project_home = '/home/djbrandy67/kibs-ims-backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables for production
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('DEBUG', 'False')

# Import your Flask application
try:
    from app import app as application
except ImportError:
    # Fallback import method
    sys.path.insert(0, os.path.join(project_home, 'app'))
    from app import app as application

# Ensure database tables are created
with application.app_context():
    try:
        from app.database import db
        db.create_all()
    except Exception as e:
        print(f"Database initialization error: {e}")

if __name__ == "__main__":
    application.run()