from functools import wraps
from flask import session, jsonify, request
from app.models import User
import jwt
from datetime import datetime, timedelta
from flask import current_app

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
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for hardcoded admin credentials
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Basic '):
                import base64
                try:
                    encoded_credentials = auth_header[6:]  # Remove 'Basic '
                    decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
                    username, password = decoded_credentials.split(':')
                    
                    # Check for hardcoded admin credentials
                    if username == 'admin' and password == 'admin123':
                        return f(*args, **kwargs)
                except Exception:
                    pass
        
        # Fall back to regular role check
        return role_required('admin')(f)(*args, **kwargs)
    return decorated_function

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

def token_required(f):
    """Decorator to check if the user has a valid token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # For hardcoded admin access, bypass token check
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Basic '):
                import base64
                try:
                    encoded_credentials = auth_header[6:]  # Remove 'Basic '
                    decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
                    username, password = decoded_credentials.split(':')
                    
                    # Check for hardcoded admin credentials
                    if username == 'admin' and password == 'admin123':
                        return f(*args, **kwargs)
                except Exception:
                    pass
        
        token = None
        
        # Check if token is in cookies
        if 'token' in request.cookies:
            token = request.cookies.get('token')
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            # Decode the token
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
            
        return f(*args, **kwargs)
    
    return decorated