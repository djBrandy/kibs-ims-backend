from flask import Flask, request, session, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from app.config import Config
import os
from datetime import datetime, timedelta


app = Flask(__name__)
app.config.from_object(Config)

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

CORS(app, 
     supports_credentials=True,
     resources={r"/*": {"origins": ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]}},
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
     expose_headers=["Access-Control-Allow-Origin"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

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


db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    product_type = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    product_code = db.Column(db.String(100), unique=True, nullable=True)
    manufacturer = db.Column(db.String(255), nullable=True)
    qr_code = db.Column(db.String(16), unique=True, nullable=False)
    price_in_kshs = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_of_measure = db.Column(db.String(50), nullable=False)
    concentration = db.Column(db.Float, nullable=True)
    storage_temperature = db.Column(db.String(255), nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    hazard_level = db.Column(db.String(255), nullable=True)
    protocol_link = db.Column(db.String(255), nullable=True)
    msds_link = db.Column(db.String(255), nullable=True)
    
    low_stock_alert = db.Column(db.Integer, default=10, nullable=False)
    checkbox_expiry_date = db.Column(db.Boolean, default=False, nullable=True)
    checkbox_hazardous_material = db.Column(db.Boolean, default=False, nullable=True)
    checkbox_controlled_substance = db.Column(db.Boolean, default=False, nullable=True)
    checkbox_requires_regular_calibration = db.Column(db.Boolean, default=False, nullable=True)
    special_instructions = db.Column(db.Text, nullable=True)
    product_images = db.Column(db.LargeBinary, nullable=True)
    date_of_entry = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    purchases = db.relationship('Purchase', backref='product', lazy=True)


class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(255), nullable=False)
    primary_contact = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    address = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    purchases = db.relationship('Purchase', backref='supplier', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'shop_name': self.shop_name,
            'primary_contact': self.primary_contact,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Purchase(db.Model):
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'supplier_id': self.supplier_id,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'quantity': self.quantity,
            'price_per_unit': self.price_per_unit,
            'total_price': self.total_price
        }


class AlertNotification(db.Model):
    __tablename__ = 'alert_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  
    last_notified = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    resolved = db.Column(db.Boolean, default=False, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'alert_type': self.alert_type,
            'last_notified': self.last_notified.isoformat() if self.last_notified else None,
            'resolved': self.resolved
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=True)  
    action_type = db.Column(db.String(50), nullable=False)  
    previous_value = db.Column(db.String(255), nullable=True)
    new_value = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    product = db.relationship('Product', backref='audit_logs', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.product_name if self.product else None,
            'action_type': self.action_type,
            'previous_value': self.previous_value,
            'new_value': self.new_value,
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class InventoryAnalytics(db.Model):
    __tablename__ = 'inventory_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    last_movement_date = db.Column(db.DateTime, nullable=True)
    days_without_movement = db.Column(db.Integer, nullable=True)
    stockout_count = db.Column(db.Integer, default=0)
    last_stockout_date = db.Column(db.DateTime, nullable=True)
    is_dead_stock = db.Column(db.Boolean, default=False)
    is_slow_moving = db.Column(db.Boolean, default=False)
    is_top_product = db.Column(db.Boolean, default=False)
    movement_rank = db.Column(db.Integer, nullable=True)  
    revenue_rank = db.Column(db.Integer, nullable=True)   
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref='analytics', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.product_name if self.product else None,
            'last_movement_date': self.last_movement_date.isoformat() if self.last_movement_date else None,
            'days_without_movement': self.days_without_movement,
            'stockout_count': self.stockout_count,
            'last_stockout_date': self.last_stockout_date.isoformat() if self.last_stockout_date else None,
            'is_dead_stock': self.is_dead_stock,
            'is_slow_moving': self.is_slow_moving,
            'is_top_product': self.is_top_product,
            'movement_rank': self.movement_rank,
            'revenue_rank': self.revenue_rank,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    products = db.relationship('Product', 
                              primaryjoin="Category.name==Product.category",
                              backref='category_rel', 
                              lazy=True,
                              foreign_keys=[Product.category])


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(255), nullable=False)
    customer_email = db.Column(db.String(255), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(50), default='pending', nullable=False)

    items = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=True) 


from routes import register_blueprints
register_blueprints(app)