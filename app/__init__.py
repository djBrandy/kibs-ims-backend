from flask import Flask, request, jsonify, redirect, g  # type: ignore
from flask_sqlalchemy import SQLAlchemy  # type: ignore
from flask_migrate import Migrate  # type: ignore
from flask_cors import CORS  # type: ignore
from flask_limiter import Limiter  # type: ignore
from flask_limiter.util import get_remote_address  # type: ignore
from flask_mail import Mail  # type: ignore
import os
import base64
from dotenv import load_dotenv  # type: ignore
from app.config import Config

# Load environment variables from .env
# load_dotenv()  # Already called in config.py, so you can remove or keep for redundancy

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

# Import models
from app.models import (
    Product, Supplier, Purchase, AlertNotification,
    AuditLog, InventoryAnalytics, Category,
    Order, OrderItem, Room, DeletedItem
)

app.url_map.strict_slashes = False

# Set up CORS with allowed origins
CORS(
    app,
    supports_credentials=True,
    origins=["http://localhost:5173"],
    allow_headers=["Content-Type", "Authorization", "x-auth-status"],
    expose_headers=["Access-Control-Allow-Origin"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# Handle preflight OPTIONS requests
@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        headers = {
            'Access-Control-Allow-Origin': request.headers.get('Origin', '*'),
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, Access-Control-Allow-Credentials, x-auth-status',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '3600'
        }
        return '', 204, headers

# Add CORS headers after each request
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Access-Control-Allow-Credentials, x-auth-status'
    return response

# Basic authentication middleware
@app.before_request
def before_request():
    if request.method == 'OPTIONS' or request.path.startswith('/api/auth/') or request.path == '/service-worker.js':
        return None

    if request.path.startswith('/api/'):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Basic '):
            try:
                from app.models import User
                encoded = auth_header.split(' ')[1]
                decoded = base64.b64decode(encoded).decode('utf-8')
                username, password = decoded.split(':', 1)
                user = User.query.filter_by(username=username).first()
                if user and user.check_password(password):
                    g.user = user
                    return None
            except Exception as e:
                app.logger.error(f"Auth error: {str(e)}")

        # Fallback to admin user for dev/test
        try:
            from sqlalchemy import inspect  # type: ignore
            inspector = inspect(db.engine)
            if 'users' in inspector.get_table_names():
                from app.models import User
                admin_user = User.query.filter_by(username='admin').first()
                if admin_user:
                    g.user = admin_user
        except Exception as e:
            app.logger.error(f"Database error: {str(e)}")
            g.user = None

# Serve the service worker if available
@app.route('/service-worker.js')
def sw():
    if os.path.exists('static/service-worker.js'):
        return app.send_static_file('service-worker.js')
    return '', 204

# Register application routes
from routes import register_routes
register_routes(app)

# Factory function for testing or scaling purposes
def create_app():
    new_app = Flask(__name__)
    new_app.config.update(app.config)
    db.init_app(new_app)
    migrate.init_app(new_app, db)
    mail.init_app(new_app)
    register_routes(new_app)
    return new_app

# Run app directly
if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
