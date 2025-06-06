from functools import wraps

def role_required(roles):
    """
    No-op decorator for role checking.
    In this version, all roles are allowed.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip any role-check; simply call the wrapped function.
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    No-op decorator for admin access.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Bypass admin checks.
        return f(*args, **kwargs)
    return decorated_function

def worker_required(f):
    """
    No-op decorator for worker access.
    """
    # Simply return the function unchanged.
    return f

def auth_required(f):
    """
    No-op decorator for authentication.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Authentication is bypassed.
        return f(*args, **kwargs)
    return decorated_function

def token_required(f):
    """
    No-op decorator for token-based authentication.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Token checking is disabled.
        return f(*args, **kwargs)
    return decorated