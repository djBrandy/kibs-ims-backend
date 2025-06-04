from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from app.models import db, User, Admin
from datetime import datetime
from sqlalchemy import text

admin_register_bp = Blueprint('admin_register', __name__, url_prefix='/api/admin-register')

@admin_register_bp.route('/', methods=['POST'])
def register_admin():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        
        print(f"Admin registration attempt: {username}, {email}")
        
        if not username or not password:
            return jsonify({"success": False, "message": "Missing required fields"}), 400
            
        # Check if admin already exists
        if Admin.query.filter_by(username=username).first() or User.query.filter_by(username=username).first():
            return jsonify({"success": False, "message": "Username already exists"}), 409
        
        # Use direct SQL for more reliable insertion
        hashed_password = generate_password_hash(password)
        current_time = datetime.utcnow()
        
        # Insert into admins table
        admin_sql = text("""
            INSERT INTO admins (username, email, phone, password_hash, created_at) 
            VALUES (:username, :email, :phone, :password_hash, :created_at)
        """)
        
        db.session.execute(admin_sql, {
            'username': username,
            'email': email,
            'phone': phone,
            'password_hash': hashed_password,
            'created_at': current_time
        })
        
        # Insert into users table
        user_sql = text("""
            INSERT INTO users (username, email, phone, password_hash, is_active, role, created_at) 
            VALUES (:username, :email, :phone, :password_hash, :is_active, :role, :created_at)
        """)
        
        db.session.execute(user_sql, {
            'username': username,
            'email': email if email else f"{username}@admin.com",
            'phone': phone,
            'password_hash': hashed_password,
            'is_active': True,
            'role': 'admin',
            'created_at': current_time
        })
        
        # Commit the transaction
        db.session.commit()
        print(f"Admin created successfully: {username}")
        
        return jsonify({
            "success": True, 
            "message": "Admin created successfully"
        })
            
    except Exception as e:
        db.session.rollback()
        import traceback
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500