from flask import Flask, request, jsonify, redirect, g  # type: ignore
from flask_sqlalchemy import SQLAlchemy  # type: ignore
from flask_migrate import Migrate  # type: ignore
from flask_cors import CORS  # type: ignore
from flask_mail import Mail  # type: ignore
import os
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
    origins=["http://localhost:5173", "https://kibs-ims.vercel.app"],
    allow_headers=["Content-Type", "Authorization", "x-auth-status"],
    expose_headers=["Access-Control-Allow-Origin"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# Authentication middleware removed:
# The "before_request" function that previously checked for tokens/Basic auth
# has been removed so that all API endpoints are publicly accessible.

# Add CORS headers after each request
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    allowed_origins = ["http://localhost:5173", "https://kibs-ims.vercel.app"]
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Access-Control-Allow-Credentials, x-auth-status'
    return response

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