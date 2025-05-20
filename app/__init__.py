from flask import Flask, request, session, jsonify, redirect # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from flask_migrate import Migrate # type: ignore
from flask_cors import CORS # type: ignore
import os
from datetime import datetime, timedelta


from .config import Config 


app = Flask(__name__)
app.config.from_object(Config)



db = SQLAlchemy(app)
migrate = Migrate(app, db)



from .models import Product, Supplier, Purchase, AlertNotification, AuditLog, InventoryAnalytics, Category, Order, OrderItem 

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
                "https://kibs-ims.netlify.app/" 
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


@app.route('/service-worker.js')
def sw():
    

    return app.send_static_file('service-worker.js')




from routes import register_blueprints 
register_blueprints(app)