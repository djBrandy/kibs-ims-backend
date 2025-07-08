#!/usr/bin/env python3
"""
Simple single-file Flask app for KIBS IMS
"""
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time
import pymysql
import json

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mysql+pymysql://djbrandy67:Brandon"
    "@djbrandy67.mysql.pythonanywhere-services.com"
    "/djbrandy67$kibs_ims_db"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'kibs-secret-key-2025'

# Initialize database
db = SQLAlchemy(app)

# CORS headers
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

# Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='worker', nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    product_type = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    product_code = db.Column(db.String(100), unique=True)
    qr_code = db.Column(db.String(16), unique=True, nullable=False)
    price_in_kshs = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_of_measure = db.Column(db.String(50), nullable=False)
    concentration = db.Column(db.Float)
    special_instructions = db.Column(db.Text)
    audit_message = db.Column(db.Text)
    force_low_stock_alert = db.Column(db.Boolean, default=False)
    last_audit_time = db.Column(db.DateTime)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    date_of_entry = db.Column(db.DateTime, default=datetime.utcnow)

class Routine(db.Model):
    __tablename__ = 'routines'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    scheduled_time = db.Column(db.Time, nullable=False)
    frequency = db.Column(db.String(20), default='daily')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Suggestion(db.Model):
    __tablename__ = 'suggestions'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='pending')
    submitted_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def home():
    return jsonify({'message': 'KIBS IMS API is running!', 'status': 'success'})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        return jsonify({
            'message': 'Login successful',
            'user': {'id': user.id, 'username': user.username, 'role': user.role}
        })
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'product_name': p.product_name,
        'product_code': p.product_code,
        'quantity': p.quantity,
        'price_in_kshs': p.price_in_kshs,
        'category': p.category,
        'audit_message': p.audit_message,
        'force_low_stock_alert': p.force_low_stock_alert
    } for p in products])

@app.route('/api/audit/scan/<barcode>', methods=['GET'])
def scan_product(barcode):
    product = Product.query.filter_by(qr_code=barcode).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify({
        'id': product.id,
        'product_name': product.product_name,
        'product_code': product.product_code,
        'quantity': product.quantity,
        'concentration': product.concentration,
        'special_instructions': product.special_instructions,
        'audit_message': product.audit_message,
        'force_low_stock_alert': product.force_low_stock_alert
    })

@app.route('/api/audit/update/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    if 'quantity' in data:
        product.quantity = int(data['quantity'])
    if 'concentration' in data:
        product.concentration = data['concentration']
    if 'special_instructions' in data:
        product.special_instructions = data['special_instructions']
    if 'audit_message' in data:
        product.audit_message = data['audit_message']
    if 'force_low_stock_alert' in data:
        product.force_low_stock_alert = bool(data['force_low_stock_alert'])
    
    product.last_audit_time = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Product updated successfully'})

@app.route('/api/routines', methods=['GET', 'POST'])
def routines():
    if request.method == 'GET':
        routines = Routine.query.filter_by(is_active=True).all()
        return jsonify([{
            'id': r.id,
            'title': r.title,
            'description': r.description,
            'scheduled_time': r.scheduled_time.strftime('%H:%M') if r.scheduled_time else None,
            'frequency': r.frequency
        } for r in routines])
    
    elif request.method == 'POST':
        data = request.get_json()
        hour, minute = map(int, data['scheduled_time'].split(':'))
        routine = Routine(
            title=data['title'],
            description=data.get('description', ''),
            scheduled_time=time(hour, minute),
            frequency=data.get('frequency', 'daily')
        )
        db.session.add(routine)
        db.session.commit()
        return jsonify({'message': 'Routine created successfully'})

@app.route('/api/suggestions', methods=['GET', 'POST'])
def suggestions():
    if request.method == 'GET':
        suggestions = Suggestion.query.all()
        return jsonify([{
            'id': s.id,
            'title': s.title,
            'description': s.description,
            'category': s.category,
            'priority': s.priority,
            'status': s.status,
            'created_at': s.created_at.isoformat()
        } for s in suggestions])
    
    elif request.method == 'POST':
        data = request.get_json()
        suggestion = Suggestion(
            title=data['title'],
            description=data['description'],
            category=data.get('category', 'general'),
            priority=data.get('priority', 'medium')
        )
        db.session.add(suggestion)
        db.session.commit()
        return jsonify({'message': 'Suggestion created successfully'})

# Create tables
with app.app_context():
    try:
        db.create_all()
        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@kibs.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
    except Exception as e:
        print(f"Database setup error: {e}")

if __name__ == '__main__':
    app.run(debug=True)