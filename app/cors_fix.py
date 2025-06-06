from flask import request

def setup_cors(app):
    """
    Set up CORS handling for the Flask app.
    This version does not allow the "Authorization" header.
    """
    allowed_origins = [
        "http://localhost:5173",
        "https://kibs-ims.vercel.app",
        "https://kibs-ims-brandons-projects-cda52e2c.vercel.app"
    ]
    
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        
        if origin and origin in allowed_origins:
            # Clear any existing CORS headers
            for header in ['Access-Control-Allow-Origin', 'Access-Control-Allow-Credentials',
                           'Access-Control-Allow-Methods', 'Access-Control-Allow-Headers']:
                if header in response.headers:
                    del response.headers[header]
            
            # Set proper CORS headers without "Authorization"
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Access-Control-Allow-Credentials, x-auth-status'
            response.headers['Vary'] = 'Origin'
        
        return response
    
    @app.before_request
    def handle_options():
        if request.method == "OPTIONS":
            origin = request.headers.get('Origin')
            
            if origin and origin in allowed_origins:
                headers = {
                    'Access-Control-Allow-Origin': origin,
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Access-Control-Allow-Credentials, x-auth-status',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Max-Age': '3600',
                    'Vary': 'Origin',
                    'Content-Type': 'text/plain'
                }
                return '', 204, headers
            
            # Default response for non-allowed origins
            return '', 204