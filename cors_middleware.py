from flask import request

class CORSMiddleware:
    def __init__(self, app, allowed_origins=None):
        self.app = app
        self.allowed_origins = allowed_origins or [
            "http://localhost:5173",
            "https://kibs-ims.vercel.app",
            "https://kibs-ims-brandons-projects-cda52e2c.vercel.app"
        ]
        
        # Register the middleware
        self.app.after_request(self.after_request)
        self.app.before_request(self.before_request)
        
    def after_request(self, response):
        origin = request.headers.get('Origin')
        
        if origin and origin in self.allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Access-Control-Allow-Credentials, x-auth-status'
            response.headers['Vary'] = 'Origin'
            
        return response
        
    def before_request(self):
        if request.method == "OPTIONS":
            origin = request.headers.get('Origin')
            
            if origin and origin in self.allowed_origins:
                headers = {
                    'Access-Control-Allow-Origin': origin,
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization, Access-Control-Allow-Credentials, x-auth-status',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Max-Age': '3600',
                    'Vary': 'Origin',
                    'Content-Type': 'text/plain'
                }
                return '', 204, headers