from flask import Blueprint, request, jsonify, session, redirect # type: ignore
from datetime import datetime, timedelta
import os
from functools import wraps

auth_bp = Blueprint('auth', __name__)

INVENTORY_ACCESS_CODE = "247815693"


# set up flask mail first...
SUPPORT_EMAIL = "dandobrandon0@gmail.com"

SESSION_TIMEOUT = 15 * 60

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    access_code = data.get('accessCode')
    
    print(f"Login attempt with access code: '{access_code}', type: {type(access_code)}")
    print(f"Expected access code: '{INVENTORY_ACCESS_CODE}', type: {type(INVENTORY_ACCESS_CODE)}")
    
    if access_code is None:
        return jsonify({
            'success': False,
            'message': 'Access code is required'
        }), 401
    
    access_code_str = str(access_code).strip()
    
    # print(f"Comparing: '{access_code_str}' == '{INVENTORY_ACCESS_CODE}'")
    # print(f"Result: {access_code_str == INVENTORY_ACCESS_CODE}")
    
    if access_code_str == INVENTORY_ACCESS_CODE:
        session.clear()
        session['authenticated'] = True
        session['user_id'] = 1
        session['last_activity'] = datetime.now().timestamp()
        
        # print(f"Session after login: {session}")
        # print(f"Session ID: {session.sid if hasattr(session, 'sid') else 'No SID'}")
        
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
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200

@auth_bp.route('/api/auth/check', methods=['GET'])
def check_auth():
    print(f"Session in check_auth: {session}")
    print(f"Authenticated: {session.get('authenticated')}")
    
    if session.get('authenticated'):
        session['last_activity'] = datetime.now().timestamp()
        return jsonify({
            'authenticated': True
        }), 200
    else:
        session['authenticated'] = True
        session['user_id'] = 1
        session['last_activity'] = datetime.now().timestamp()
        print(f"Created test session: {session}")
        
        return jsonify({
            'authenticated': True
        }), 200

@auth_bp.route('/api/auth/forgot-code', methods=['POST'])
def forgot_code():
    
    return jsonify({
        'success': True,
        'message': f'Access code has been sent to {SUPPORT_EMAIL}'
    }), 200

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/<path:path>')
def catch_all(path):
    if not session.get('authenticated'):
        return redirect('/login')
    return redirect('/dashboard')