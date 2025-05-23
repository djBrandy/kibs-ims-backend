from flask import Flask, request, jsonify, redirect, g # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from flask_migrate import Migrate # type: ignore
from flask_cors import CORS # type: ignore
from flask_limiter import Limiter # type: ignore
from flask_limiter.util import get_remote_address # type: ignore
from flask_mail import Mail # type: ignore
import os
from datetime import datetime
from dotenv import load_dotenv # type: ignore

load_dotenv()

# from .config import Config 


app = Flask(__name__)
# app.config.from_object(Config)


# Database configuration
database_url = os.getenv('DATABASE_URL', 'postgresql://kibs_user:Xe9TM4q9axDuN5CFBEffX6H4V9kTdMcr@dpg-d0nidt8dl3ps73aabl0g-a/kibs_ims')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Fix for SQLAlchemy 2.0 compatibility
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 900
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'kibs-ims-secret-key')
app.config['DEBUG'] = os.getenv('DEBUG', 'False') == 'True'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 900
app.config['FRONTEND_URL'] = os.getenv('FRONTEND_URL', 'https://kibs-ims.netlify.app')





db = SQLAlchemy(app)
migrate = Migrate(app, db)



# Import models after db is initialized
from app.models import Product, Supplier, Purchase, AlertNotification, AuditLog, InventoryAnalytics, Category, Order, OrderItem

app.url_map.strict_slashes = False

app.secret_key = os.environ.get('SECRET_KEY', 'kibs-ims-secret-key')


# FRONTEND_URL = app.config.get('FRONTEND_URL', 'https://kibs-ims.netlify.app')

CORS(
    app,
    supports_credentials=True,
    resources={
        r"/*": {
            "origins": [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                'https://kibs-ims.netlify.app'
                # FRONTEND_URL
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
    allowed_origins = [
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://127.0.0.1:5173", 
        'https://kibs-ims.netlify.app',
        '*'
        ]
    
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
    
    # Skip auth check for service worker
    if request.path == '/service-worker.js':
        return None
    
    # Implement proper authentication for production
    if request.path.startswith('/api/'):
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Basic '):
            # Handle Basic Auth
            try:
                from app.models import User
                import base64
                
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
        
        # For development/testing, bypass auth check
        try:
            # Check if users table exists before querying
            from sqlalchemy import inspect # type: ignore
            inspector = inspect(db.engine)
            if 'users' in inspector.get_table_names():
                from app.models import User
                admin_user = User.query.filter_by(username='admin').first()
                if admin_user:
                    g.user = admin_user
        except Exception as e:
            app.logger.error(f"Database error: {str(e)}")
            # Allow request to continue even if users table doesn't exist
            g.user = None


@app.route('/service-worker.js')
def sw():
    # Return actual service worker content
    response = app.send_static_file('service-worker.js') if os.path.exists('static/service-worker.js') else ('', 204)
    return response
    

# limiter = Limiter(app, key_func=get_remote_address) # type: ignore
mail = Mail()

from routes import register_routes 
register_routes(app)

def create_app():
    app = Flask(__name__)
    mail.init_app(app)
    
    return app