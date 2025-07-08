#!/usr/bin/env python3
import sys
import os
import traceback

# Add your project directory to the Python path
project_home = '/home/djbrandy67/kibs-ims-backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

print("Python path:", sys.path)
print("Current working directory:", os.getcwd())
print("Project home exists:", os.path.exists(project_home))

try:
    print("Attempting to import app...")
    from app import app as application
    print("Successfully imported app!")
except Exception as e:
    print("Error importing app:")
    print("Exception type:", type(e).__name__)
    print("Exception message:", str(e))
    print("Full traceback:")
    traceback.print_exc()
    
    # Try to import individual modules to debug
    try:
        print("\nTrying to import Flask...")
        import flask
        print("Flask imported successfully")
    except Exception as flask_error:
        print("Flask import failed:", flask_error)
    
    try:
        print("\nTrying to import app.config...")
        from app.config import Config
        print("Config imported successfully")
    except Exception as config_error:
        print("Config import failed:", config_error)
    
    try:
        print("\nTrying to import app.database...")
        from app.database import db
        print("Database imported successfully")
    except Exception as db_error:
        print("Database import failed:", db_error)
    
    # Create a minimal application as fallback
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def hello():
        return "Debug mode - check error logs for details"

if __name__ == "__main__":
    application.run()