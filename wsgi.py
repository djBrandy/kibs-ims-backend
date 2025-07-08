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

# Import your Flask application
from app import app as application

if __name__ == "__main__":
    application.run()