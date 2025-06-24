from flask import Flask, request, make_response # type: ignore

def add_cors_headers(response):
    """Add CORS headers to all responses"""
    origin = request.headers.get('Origin')
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1"
    ]
    
    if origin and origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Access-Control-Allow-Credentials, x-auth-status, ngrok-skip-browser-warning'
        response.headers['Access-Control-Max-Age'] = '3600'
        response.headers['Vary'] = 'Origin'
    
    return response

def handle_options_request():
    """Handle OPTIONS requests explicitly"""
    if request.method == 'OPTIONS':
        origin = request.headers.get('Origin')
        allowed_origins = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1"
        ]
        
        if origin and origin in allowed_origins:
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Access-Control-Allow-Credentials, x-auth-status, ngrok-skip-browser-warning'
            response.headers['Access-Control-Max-Age'] = '3600'
            response.headers['Vary'] = 'Origin'
            response.headers['Content-Type'] = 'text/plain'
            return response
    
    return None

def setup_cors(app):
    """Set up CORS handling for the Flask app"""
    # Register after_request handler to add CORS headers to all responses
    app.after_request(add_cors_headers)
    
    # Register before_request handler to handle OPTIONS requests
    @app.before_request
    def before_request_func():
        options_response = handle_options_request()
        if options_response:
            return options_response