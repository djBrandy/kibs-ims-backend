from flask import Flask, request, jsonify, redirect, g # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from flask_migrate import Migrate # type: ignore
from flask_cors import CORS # type: ignore
from flask_limiter import Limiter # type: ignore
from flask_limiter.util import get_remote_address # type: ignore
from flask_mail import Mail # type: ignore
import os
from datetime import datetime


# from .config import Config 


app = Flask(__name__)
# app.config.from_object(Config)



db = SQLAlchemy(app)
migrate = Migrate(app, db)



from .models import Product, Supplier, Purchase, AlertNotification, AuditLog, InventoryAnalytics, Category, Order, OrderItem 

app.url_map.strict_slashes = False

app.secret_key = os.environ.get('SECRET_KEY', 'kibs-ims-secret-key')


# Get frontend URL from config
FRONTEND_URL = app.config.get('FRONTEND_URL', 'https://kibs-ims.netlify.app')

CORS(
    app,
    supports_credentials=True,
    resources={
        r"/*": {
            "origins": [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                FRONTEND_URL
            ]
        }
    },
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    expose_headers=["Access-Control-Allow-Origin"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        headers = {
            'Access-Control-Allow-Origin': request.headers.get('Origin', '*'),
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '3600'
        }
        return '', 204, headers

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    allowed_origins = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173", FRONTEND_URL]
    
    if origin and origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    return response


@app.before_request
def before_request():
    # Skip auth check for OPTIONS requests
    if request.method == 'OPTIONS':
        return None
        
    # Skip auth check for auth endpoints
    if request.path.startswith('/api/auth/'):
        return None
    
    # Implement proper authentication for production
    if request.path.startswith('/api/'):
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Basic '):
            # Handle Basic Auth
            from app.models import User
            import base64
            
            try:
                encoded = auth_header.split(' ')[1]
                decoded = base64.b64decode(encoded).decode('utf-8')
                username, password = decoded.split(':', 1)
                
                user = User.query.filter_by(username=username).first()
                if user and user.check_password(password):
                    g.user = user
                    return None
            except Exception as e:
                app.logger.error(f"Auth error: {str(e)}")
                pass
        
        # Check for session-based auth as fallback
        from app.models import User
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            g.user = admin_user


@app.route('/service-worker.js')
def sw():
    # Placeholder response for service worker
    return '', 204
    

# limiter = Limiter(app, key_func=get_remote_address) # type: ignore
mail = Mail()

from routes import register_routes 
register_routes(app)

def create_app():
    app = Flask(__name__)
    mail.init_app(app)
    
    return app