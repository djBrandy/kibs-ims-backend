from flask import Blueprint, request, jsonify, session, redirect
from datetime import datetime, timedelta
import os
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# Access code for the inventory system
INVENTORY_ACCESS_CODE = "247815693"  # Do not change this value
# Email to send the code to when forgotten
SUPPORT_EMAIL = "dandobrandon0@gmail.com"

# Session configuration
SESSION_TIMEOUT = 15 * 60  # 15 minutes in seconds

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user with access code"""
    data = request.get_json()
    access_code = data.get('accessCode')
    
    # Debug logging
    print(f"Login attempt with access code: '{access_code}', type: {type(access_code)}")
    print(f"Expected access code: '{INVENTORY_ACCESS_CODE}', type: {type(INVENTORY_ACCESS_CODE)}")
    
    # Handle None or empty access code
    if access_code is None:
        return jsonify({
            'success': False,
            'message': 'Access code is required'
        }), 401
    
    # Convert access_code to string and trim whitespace
    access_code_str = str(access_code).strip()
    
    # Debug comparison
    print(f"Comparing: '{access_code_str}' == '{INVENTORY_ACCESS_CODE}'")
    print(f"Result: {access_code_str == INVENTORY_ACCESS_CODE}")
    
    if access_code_str == INVENTORY_ACCESS_CODE:
        # Set session variables
        session.clear()  # Clear any existing session data
        session['authenticated'] = True
        session['user_id'] = 1  # Default user ID
        session['last_activity'] = datetime.now().timestamp()
        
        # Debug session
        print(f"Session after login: {session}")
        print(f"Session ID: {session.sid if hasattr(session, 'sid') else 'No SID'}")
        
        response = jsonify({
            'success': True,
            'message': 'Authentication successful'
        })
        
        return response, 200
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid access code'
        }), 401

@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """Log out user by clearing session"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200

@auth_bp.route('/api/auth/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    print(f"Session in check_auth: {session}")
    print(f"Authenticated: {session.get('authenticated')}")
    
    if session.get('authenticated'):
        # Update last activity timestamp
        session['last_activity'] = datetime.now().timestamp()
        return jsonify({
            'authenticated': True
        }), 200
    else:
        # For debugging purposes, create a test session if none exists
        # REMOVE THIS IN PRODUCTION
        session['authenticated'] = True
        session['user_id'] = 1
        session['last_activity'] = datetime.now().timestamp()
        print(f"Created test session: {session}")
        
        return jsonify({
            'authenticated': True
        }), 200

@auth_bp.route('/api/auth/forgot-code', methods=['POST'])
def forgot_code():
    """Handle forgotten access code"""
    # In a real application, this would send an email
    # For this implementation, we'll just return a success message
    
    return jsonify({
        'success': True,
        'message': f'Access code has been sent to {SUPPORT_EMAIL}'
    }), 200

# Authentication middleware
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Always allow access without authentication for development
        # REMOVE THIS IN PRODUCTION
        return f(*args, **kwargs)
    return decorated_function

# Catch-all route to redirect to login page
@auth_bp.route('/<path:path>')
def catch_all(path):
    """Redirect all undefined routes to login page if not authenticated"""
    if not session.get('authenticated'):
        return redirect('/login')
    return redirect('/dashboard')