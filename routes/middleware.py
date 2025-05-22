from functools import wraps
from flask import session, jsonify, request
from app.models import User

def role_required(roles):
    """
    Decorator to check if the user has the required role(s)
    
    Args:
        roles: A string or list of strings representing the required role(s)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            user_role = session.get('role')
            
            if not user_id or not user_role:
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            
            # Convert roles to list if it's a string
            required_roles = roles if isinstance(roles, list) else [roles]
            
            if user_role not in required_roles:
                return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to check if the user is an admin"""
    return role_required('admin')(f)

def worker_required(f):
    """Decorator to check if the user is a worker"""
    return role_required('worker')(f)

def auth_required(f):
    """Decorator to check if the user is authenticated"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function