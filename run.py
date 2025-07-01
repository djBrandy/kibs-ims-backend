#!/usr/bin/env python3
"""
Simple startup script for the KIBS IMS Backend
Usage: python run.py
"""

from app import app
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting KIBS IMS Backend on port {port}")
    print(f"Debug mode: {debug}")
    print("Admin user will be created automatically if it doesn't exist")
    print("Default admin credentials: admin/admin123")
    
    app.run(host='0.0.0.0', port=port, debug=debug)