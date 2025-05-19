from flask import Flask, request, session, jsonify, redirect # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from flask_migrate import Migrate # type: ignore
from flask_cors import CORS # type: ignore
import os
from datetime import datetime, timedelta

# Configuration should be imported before creating the app instance if it's used by app creation.
from .config import Config # Changed to relative import

app = Flask(__name__)
app.config.from_object(Config)

# Initialize SQLAlchemy and Migrate AFTER app is created and configured,
# but BEFORE models are imported.
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Now import models (they need 'db' from above)
from .models import Product, Supplier, Purchase, AlertNotification, AuditLog, InventoryAnalytics, Category, Order, OrderItem # Changed to relative import

app.url_map.strict_slashes = False

app.secret_key = os.environ.get('SECRET_KEY', 'kibs-ims-secret-key')

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)
app.config['SESSION_COOKIE_SECURE'] = True  
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_DOMAIN'] = None  
app.config['SESSION_COOKIE_NAME'] = 'kibs_session'  


app.config['SESSION_COOKIE_NAME'] = 'kibs_session'


CORS(
    app,
    supports_credentials=True,
    resources={
        r"/*": {
            "origins": [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "https://kibs-ims.netlify.app/"  # Add your production URL here
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
    allowed_origins = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    
    if origin and origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    if 'Set-Cookie' in response.headers:
        print(f"Setting cookie: {response.headers['Set-Cookie']}")
    
    return response


@app.before_request
def check_session_timeout():
    
    return None

# Route to serve the service worker from the root
@app.route('/service-worker.js')
def sw():
    # By default, app.static_folder is 'static' relative to app.root_path (i.e., 'app/static/')
    return app.send_static_file('service-worker.js')


# Blueprints
from routes import register_blueprints # Use absolute import for sibling package
register_blueprints(app)