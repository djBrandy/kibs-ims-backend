from app import db
# from flask_sqlalchemy import SQLAlchemy # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer # type: ignore
from flask import current_app # type: ignore



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
    hidden_from_workers = db.Column(db.Boolean, default=False)
    
    purchases = db.relationship('Purchase', backref='product', lazy=True)
    
    def to_dict(self, include_qr=True):
        data = {
            'id': self.id,
            'product_name': self.product_name,
            'product_type': self.product_type,
            'category': self.category,
            'product_code': self.product_code,
            'manufacturer': self.manufacturer,
            'price_in_kshs': self.price_in_kshs,
            'quantity': self.quantity,
            'unit_of_measure': self.unit_of_measure,
            'concentration': self.concentration,
            'storage_temperature': self.storage_temperature,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'hazard_level': self.hazard_level,
            'protocol_link': self.protocol_link,
            'msds_link': self.msds_link,
            'low_stock_alert': self.low_stock_alert,
            'checkbox_expiry_date': self.checkbox_expiry_date,
            'checkbox_hazardous_material': self.checkbox_hazardous_material,
            'checkbox_controlled_substance': self.checkbox_controlled_substance,
            'checkbox_requires_regular_calibration': self.checkbox_requires_regular_calibration,
            'special_instructions': self.special_instructions,
            'date_of_entry': self.date_of_entry.isoformat() if self.date_of_entry else None
        }
        
        # Add hidden_from_workers if it exists
        try:
            if hasattr(self, 'hidden_from_workers'):
                data['hidden_from_workers'] = self.hidden_from_workers
        except:
            pass
        
        # Only include QR code for admin users
        if include_qr:
            data['qr_code'] = self.qr_code
            
        return data


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
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }


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


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Worker(db.Model):
    __tablename__ = 'workers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PasswordResetCode(db.Model):
    __tablename__ = 'password_reset_codes'
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(10), nullable=False)  # 'admin' or 'worker'
    user_id = db.Column(db.Integer, nullable=False)
    code = db.Column(db.String(8), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

class MFACode(db.Model):
    __tablename__ = 'mfa_codes'
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(10), nullable=False)  # 'admin' or 'worker'
    user_id = db.Column(db.Integer, nullable=False)
    code = db.Column(db.String(8), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    reset_token = db.Column(db.String(128), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='worker')
    permissions = db.Column(db.Text, nullable=True)  # JSON string for custom permissions
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.Text, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expiration=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=expiration)
        except Exception:
            return None
        return User.query.get(data['user_id'])

class PendingDelete(db.Model):
    __tablename__ = 'pending_deletes'
    
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    
    # Relationships
    worker = db.relationship('User', backref='delete_requests')
    product = db.relationship('Product', backref='delete_requests')
    
    def to_dict(self):
        return {
            'id': self.id,
            'worker_id': self.worker_id,
            'worker_name': self.worker.username if self.worker else 'Unknown',
            'product_id': self.product_id,
            'product_name': self.product.product_name if self.product else 'Unknown',
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'status': self.status
        }