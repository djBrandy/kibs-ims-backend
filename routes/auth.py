from flask import Blueprint, request, jsonify, current_app, g, session # type: ignore
from flask_limiter import Limiter # type: ignore
from flask_limiter.util import get_remote_address # type: ignore
from datetime import datetime, timedelta
import re, random, string, logging, json, base64
from functools import wraps
from app.models import db, Admin, Worker, PasswordResetCode, MFACode, Product, Supplier, User, AuditLog, Category, Purchase, PendingDelete
from sqlalchemy import text
from app.utils import send_email, send_sms_africastalking
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore

from sqlalchemy import func # type: ignore

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
limiter = Limiter(key_func=get_remote_address)

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
PHONE_REGEX = re.compile(r"^\+?\d{10,15}$")
ADMIN_ACCESS_CODE = "247815693"

# Debug function to print session info
def debug_session():
    print(f"SESSION: {dict(session)}")
    print(f"USER_ID: {session.get('user_id')}")
    print(f"ROLE: {session.get('role')}")

# Simple auth middleware
def get_auth_user():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '):
        return None
    
    try:
        # Extract and decode credentials
        encoded_credentials = auth_header[6:]  # Remove 'Basic '
        decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded_credentials.split(':')
        
        # Check for hardcoded admin credentials
        if username == 'admin' and password == 'admin123':
            # Find or create admin user
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                return admin_user
            else:
                # Create admin user if it doesn't exist
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    role='admin',
                    is_active=True
                )
                admin_user.password_hash = generate_password_hash('admin123')
                db.session.add(admin_user)
                db.session.commit()
                return admin_user
        
        # Regular user authentication
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            return user
    except Exception as e:
        logging.error(f"Auth error: {e}")
    
    return None

# Define decorators at the top of the file
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For debugging, allow all requests
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For debugging, allow all requests with hardcoded admin credentials
        return f(*args, **kwargs)
    return decorated_function

def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

def validate_email(email):
    return EMAIL_REGEX.match(email)

def validate_phone(phone):
    return PHONE_REGEX.match(phone)

@auth_bp.route('/signup', methods=['POST'])
@limiter.limit("5/minute")
def signup():
    try:
        data = request.json
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        phone = data.get('phone', '').strip()

        print(f"Signup attempt: {username}, {email}")

        if not username or not email or not password:
            return jsonify({"success": False, "message": "Missing required fields."}), 400
        if not validate_email(email):
            return jsonify({"success": False, "message": "Invalid email format."}), 400
        if phone and not validate_phone(phone):
            return jsonify({"success": False, "message": "Invalid phone number."}), 400

        # Check if worker already exists
        if Worker.query.filter((Worker.username == username)|(Worker.email == email)).first():
            return jsonify({"success": False, "message": "Username or email already exists."}), 409
        
        # Check if user already exists in User table
        if User.query.filter((User.username == username)|(User.email == email)).first():
            return jsonify({"success": False, "message": "Username or email already exists in User table."}), 409

        # Test direct SQL connection
        try:
            result = db.session.execute(text("SELECT 1"))
            print(f"Database connection test: {list(result)}")
        except Exception as db_error:
            print(f"Database connection error: {str(db_error)}")
            return jsonify({"success": False, "message": f"Database connection error: {str(db_error)}"}), 500

        # Create user with direct SQL
        hashed_password = generate_password_hash(password)
        current_time = datetime.utcnow()
        
        try:
            # Insert into users table
            user_sql = text("""
                INSERT INTO users (username, email, phone, password_hash, is_active, role, created_at) 
                VALUES (:username, :email, :phone, :password_hash, :is_active, :role, :created_at)
            """)
            
            db.session.execute(user_sql, {
                'username': username,
                'email': email,
                'phone': phone,
                'password_hash': hashed_password,
                'is_active': True,
                'role': 'worker',
                'created_at': current_time
            })
            
            # Insert into workers table
            worker_sql = text("""
                INSERT INTO workers (username, email, phone, password_hash, is_active, created_at) 
                VALUES (:username, :email, :phone, :password_hash, :is_active, :created_at)
            """)
            
            db.session.execute(worker_sql, {
                'username': username,
                'email': email,
                'phone': phone,
                'password_hash': hashed_password,
                'is_active': True,
                'created_at': current_time
            })
            
            # Commit the transaction
            db.session.commit()
            print(f"Direct SQL insert successful for user: {username}")
            
            # Verify with direct SQL
            verify_sql = text("SELECT id, username FROM users WHERE username = :username")
            result = db.session.execute(verify_sql, {'username': username}).fetchone()
            
            if result:
                print(f"Verification successful: User {username} found with ID {result[0]}")
                return jsonify({"success": True, "message": "Worker registered successfully."})
            else:
                print(f"WARNING: User {username} not found after direct SQL insert!")
                return jsonify({"success": False, "message": "User created but not found in verification."}), 500
                
        except Exception as sql_error:
            db.session.rollback()
            print(f"SQL error: {str(sql_error)}")
            import traceback
            print(traceback.format_exc())
            return jsonify({"success": False, "message": f"Database SQL error: {str(sql_error)}"}), 500
    except Exception as e:
        db.session.rollback()
        import traceback
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    print(f"Login attempt: {username}")

    # Check for hardcoded admin credentials
    if username == 'admin' and password == 'admin123':
        # Find or create admin user
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            # Update last login time
            admin_user.last_login = datetime.utcnow()
            admin_user.last_activity = datetime.utcnow()
            db.session.commit()
            
            # Log the login
            try:
                login_log = LoginLog(
                    user_id=admin_user.id,
                    status='success',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(login_log)
                db.session.commit()
            except Exception as e:
                print(f"Error logging login: {e}")
            
            return jsonify({
                'success': True, 
                'role': 'admin', 
                'userId': admin_user.id
            }), 200
        else:
            # Create admin user if it doesn't exist
            admin_user = User(
                username='admin',
                email='admin@example.com',
                role='admin',
                is_active=True,
                last_login=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
            admin_user.password_hash = generate_password_hash('admin123')
            db.session.add(admin_user)
            db.session.commit()
            
            # Log the login
            try:
                login_log = LoginLog(
                    user_id=admin_user.id,
                    status='success',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(login_log)
                db.session.commit()
            except Exception as e:
                print(f"Error logging login: {e}")
            
            return jsonify({
                'success': True, 
                'role': 'admin', 
                'userId': admin_user.id
            }), 200
    
    # Regular user authentication flow
    user = User.query.filter_by(username=username).first()
    print(f"User found: {user is not None}")
    if user:
        print(f"Password hash: {user.password_hash}")
        print(f"Password check: {check_password_hash(user.password_hash, password)}")
    if user and check_password_hash(user.password_hash, password):
        # Update last login time
        user.last_login = datetime.utcnow()
        user.last_activity = datetime.utcnow()
        db.session.commit()
        
        # Log the login
        try:
            login_log = LoginLog(
                user_id=user.id,
                status='success',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(login_log)
            db.session.commit()
        except Exception as e:
            print(f"Error logging login: {e}")
        
        return jsonify({
            'success': True, 
            'role': user.role, 
            'userId': user.id
        }), 200

    # If not found in User table, check Worker table as fallback
    worker = Worker.query.filter_by(username=username).first()
    if worker and worker.check_password(password):
        # Create a User entry for this worker to ensure future logins work
        new_user = User(
            username=worker.username,
            email=worker.email,
            phone=worker.phone,
            role='worker',
            is_active=True,
            last_login=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        new_user.password_hash = worker.password_hash  # Copy the password hash
        db.session.add(new_user)
        db.session.commit()
        
        # Log the login
        try:
            login_log = LoginLog(
                user_id=new_user.id,
                status='success',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(login_log)
            db.session.commit()
        except Exception as e:
            print(f"Error logging login: {e}")
        
        return jsonify({
            'success': True, 
            'role': 'worker', 
            'userId': new_user.id
        }, 200)
    
    # Log failed login attempt
    try:
        # Find user by username for logging purposes
        target_user = User.query.filter_by(username=username).first()
        if target_user:
            login_log = LoginLog(
                user_id=target_user.id,
                status='failed',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(login_log)
            db.session.commit()
    except Exception as e:
        print(f"Error logging failed login: {e}")

    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@auth_bp.route('/verify-mfa', methods=['POST'])
@limiter.limit("10/minute")
def verify_mfa():
    data = request.json
    user_type = data.get('user_type')
    user_id = data.get('user_id')
    code = data.get('code')

    mfa = MFACode.query.filter_by(user_type=user_type, user_id=user_id, code=code, used=False).first()
    if not mfa or mfa.expires_at < datetime.utcnow():
        return jsonify({"success": False, "message": "Invalid or expired MFA code."}), 401

    mfa.used = True
    db.session.commit()
    
    # Find the user
    if user_type == 'admin':
        user = Admin.query.get(user_id)
    else:
        user = Worker.query.get(user_id)
    
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404
    
    # Create credentials string for Basic Auth
    credentials = f"{user.username}:{user.password}"  # This is not secure, just for demo
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    return jsonify({
        "success": True, 
        "auth": f"Basic {encoded_credentials}"
    })

@auth_bp.route('/forgot-code', methods=['POST'])
@limiter.limit("3/minute")
def forgot_code():
    data = request.json
    username = data.get('username', '').strip()
    user_type = data.get('user_type', 'worker')

    if user_type == 'admin':
        user = Admin.query.filter_by(username=username).first()
        if not user:
            return jsonify({"success": False, "message": "Admin not found."}), 404
        code = generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        reset = PasswordResetCode(user_type='admin', user_id=user.id, code=code, expires_at=expires_at)
        db.session.add(reset)
        db.session.commit()
        try:
            send_sms_africastalking(user.phone, f"Your admin password reset code: {code}")
        except Exception as e:
            logging.error(f"Failed to send SMS: {e}")
        return jsonify({"success": True, "message": "Reset code sent via SMS."})
    else:
        user = Worker.query.filter_by(username=username).first()
        if not user:
            return jsonify({"success": False, "message": "Worker not found."}), 404
        code = generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        reset = PasswordResetCode(user_type='worker', user_id=user.id, code=code, expires_at=expires_at)
        db.session.add(reset)
        db.session.commit()
        try:
            send_email(user.email, "Password Reset Code", f"Your password reset code: {code}")
        except Exception as e:
            logging.error(f"Failed to send email: {e}")
        return jsonify({"success": True, "message": "Reset code sent via email."})

@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit("3/minute")
def reset_password():
    data = request.json
    user_type = data.get('user_type')
    username = data.get('username', '').strip()
    code = data.get('code')
    new_password = data.get('new_password')

    if user_type == 'admin':
        user = Admin.query.filter_by(username=username).first()
    else:
        user = Worker.query.filter_by(username=username).first()

    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    reset = PasswordResetCode.query.filter_by(user_type=user_type, user_id=user.id, code=code, used=False).first()
    if not reset or reset.expires_at < datetime.utcnow():
        return jsonify({"success": False, "message": "Invalid or expired reset code."}), 401

    user.set_password(new_password)
    reset.used = True
    db.session.commit()
    return jsonify({"success": True, "message": "Password reset successful."})

@auth_bp.route('/admin-access', methods=['POST'])
@login_required
def admin_access():
    data = request.get_json()
    code = data.get('code')
    user = g.user
    
    if code == ADMIN_ACCESS_CODE:
        # Update the user's role in the database
        user.role = 'admin'
        db.session.commit()
        


        log_entry = AuditLog(
            product_id=1,  
            user_id=user.id,
            action_type='role_change',
            previous_value='worker',
            new_value='admin',
            notes=f"User {user.id} changed role to admin"
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "role": "admin"
        }), 200
    return jsonify({"success": False, "message": "Invalid access code"}), 401

@auth_bp.route('/re-auth', methods=['POST'])
@login_required
def re_auth():
    data = request.get_json()
    password = data.get('password')
    user = g.user
    
    if not password:
        return jsonify({'success': False, 'message': 'Missing password'}), 400

    if check_password_hash(user.password_hash, password):
        # Create credentials string for Basic Auth
        credentials = f"{user.username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        return jsonify({
            'success': True, 
            'role': user.role,
            'auth': f"Basic {encoded_credentials}"
        }), 200
    return jsonify({'success': False, 'message': 'Invalid password'}), 401

@auth_bp.route('/check', methods=['GET'])
def check_auth():
    # Always return authenticated as admin with hardcoded credentials
    return jsonify({
        'authenticated': True,
        'role': 'admin',
        'userId': 1
    }), 200

@auth_bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard_data():
    user = g.user
    user_id = user.id
    user_role = user.role

    if user_role == 'worker':
        # Workers see products in stock and supplier info in the same format as admin
        # But exclude products that are hidden from workers if the column exists
        try:
            products = [p.to_dict(include_qr=False) for p in Product.query.filter(
                Product.quantity > 0, 
                Product.hidden_from_workers == False
            ).all()]
        except Exception:
            # Fallback if hidden_from_workers column doesn't exist
            products = [p.to_dict(include_qr=False) for p in Product.query.filter(
                Product.quantity > 0
            ).all()]
        suppliers = [s.to_dict() for s in Supplier.query.all()]
        categories = [c.to_dict() for c in Category.query.all()]
        
        # Get worker permissions
        user = User.query.get(user_id)
        permissions = {
            'can_add_products': True,
            'can_update_products': True,
            'can_delete_products': True  # Allow workers to "delete" (request deletion)
        }
        if user and hasattr(user, 'permissions') and user.permissions:
            try:
                custom_permissions = json.loads(user.permissions)
                permissions.update(custom_permissions)
            except:
                pass
                
        return jsonify({
            'role': user_role,
            'products': products,
            'suppliers': suppliers,
            'categories': categories,
            'permissions': permissions
        }), 200

    elif user_role == 'admin':
        # Admins can see everything including QR codes
        products = [p.to_dict(include_qr=True) for p in Product.query.all()]
        suppliers = [s.to_dict() for s in Supplier.query.all()]
        
        # Get pending delete requests if table exists
        pending_deletes = []
        try:
            for request in PendingDelete.query.filter_by(status='pending').all():
                product = Product.query.get(request.product_id)
                worker = User.query.get(request.worker_id)
                if product and worker:
                    pending_deletes.append({
                        'id': request.id,
                        'product_id': request.product_id,
                        'product_name': product.product_name,
                        'worker_id': request.worker_id,
                        'worker_name': worker.username,
                        'timestamp': request.timestamp.isoformat(),
                        'message': f"Worker {worker.username} is attempting to delete product {product.product_name}."
                    })
        except Exception:
            # If table doesn't exist yet, continue with empty list
            pass
        
        # Enhanced worker list with analytics
        workers_data = []
        workers = User.query.filter_by(role='worker').all()
        
        for worker in workers:
            # Count audits by this worker
            audit_count = AuditLog.query.filter_by(user_id=worker.id).count()
            
            # Get last activity time
            last_activity = worker.last_activity.isoformat() if worker.last_activity else None
            
            # Calculate time spent in app (if available)
            time_in_app = None
            if worker.last_activity and worker.last_login:
                time_diff = worker.last_activity - worker.last_login
                time_in_app = time_diff.total_seconds() / 60  # minutes
            
            # Get permissions
            permissions = {}
            if worker.permissions:
                try:
                    permissions = json.loads(worker.permissions)
                except:
                    pass
            
            workers_data.append({
                'id': worker.id,
                'username': worker.username,
                'email': worker.email,
                'phone': worker.phone,
                'is_active': worker.is_active,
                'is_banned': worker.is_banned if hasattr(worker, 'is_banned') else False,
                'ban_reason': worker.ban_reason if hasattr(worker, 'ban_reason') else None,
                'created_at': worker.created_at.isoformat() if worker.created_at else None,
                'last_login': worker.last_login.isoformat() if worker.last_login else None,
                'last_activity': last_activity,
                'time_in_app': time_in_app,
                'audit_count': audit_count,
                'permissions': permissions
            })
        
        # Sort workers by activity (most active first)
        workers_data.sort(key=lambda w: w['audit_count'] if w['audit_count'] else 0, reverse=True)
        
        # Get login logs from AuditLog table
        login_logs = [
            {
                'id': log.id,
                'user_id': log.user_id,
                'username': User.query.get(log.user_id).username if User.query.get(log.user_id) else 'Unknown',
                'timestamp': log.timestamp.isoformat(),
                'action': log.action_type,
                'notes': log.notes
            }
            for log in AuditLog.query.filter_by(action_type='login').order_by(AuditLog.timestamp.desc()).limit(50).all()
        ]
        
        # Get stock alerts for products with low quantity
        stock_alerts = [
            {
                'id': p.id,
                'product_name': p.product_name,
                'quantity': p.quantity,
                'low_stock_alert': p.low_stock_alert
            }
            for p in Product.query.filter(Product.quantity <= Product.low_stock_alert).all()
        ]
        
        # Get inventory analytics
        inventory_analytics = {
            'total_products': Product.query.count(),
            'low_stock_count': len(stock_alerts),
            'out_of_stock': Product.query.filter(Product.quantity == 0).count(),
            'categories_count': Category.query.count()
        }
        
        # Get audit logs
        audit_logs = [log.to_dict() for log in AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()]
        
        # Get product creation history
        product_creation_history = [
            {
                'id': log.id,
                'product_id': log.product_id,
                'product_name': log.product.product_name if log.product else 'Unknown',
                'timestamp': log.timestamp.isoformat(),
                'action': log.action_type
            }
            for log in AuditLog.query.filter_by(action_type='create').order_by(AuditLog.timestamp.desc()).limit(20).all()
        ]
        
        categories = [c.to_dict() for c in Category.query.all()]
        
        # Add "What's Going On" section
        whats_going_on = {
            'recent_logins': [log for log in login_logs[:5]],
            'recent_audits': [log.to_dict() for log in AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(5).all()],
            'recent_products': [p.to_dict() for p in Product.query.order_by(Product.date_of_entry.desc()).limit(5).all()],
            'active_workers': [w for w in workers_data if w['last_activity'] is not None][:5],
            'system_stats': {
                'total_products': Product.query.count(),
                'total_workers': User.query.filter_by(role='worker').count(),
                'total_audits': AuditLog.query.count(),
                'total_suppliers': Supplier.query.count()
            }
        }
        
        # Add AI-based predictive restocking suggestions
        predictive_restocking = []
        low_stock_products = Product.query.filter(Product.quantity <= Product.low_stock_alert).all()
        
        for product in low_stock_products:
            # Simple prediction algorithm (can be enhanced with ML)
            recent_purchases = Purchase.query.filter_by(product_id=product.id).order_by(Purchase.purchase_date.desc()).limit(3).all()
            if recent_purchases:
                avg_time_between_purchases = 30  # Default 30 days
                if len(recent_purchases) > 1:
                    # Calculate average time between purchases
                    time_diffs = []
                    for i in range(len(recent_purchases)-1):
                        time_diff = recent_purchases[i].purchase_date - recent_purchases[i+1].purchase_date
                        time_diffs.append(time_diff.days)
                    if time_diffs:
                        avg_time_between_purchases = sum(time_diffs) / len(time_diffs)
                
                predictive_restocking.append({
                    'product_id': product.id,
                    'product_name': product.product_name,
                    'current_quantity': product.quantity,
                    'suggested_restock_date': (datetime.utcnow() + timedelta(days=avg_time_between_purchases)).isoformat(),
                    'suggested_quantity': int(product.low_stock_alert * 2),  # Simple suggestion
                    'confidence': 'medium'  # Placeholder for ML confidence
                })
        
        return jsonify({
            'role': user_role,
            'products': products,
            'suppliers': suppliers,
            'workers': workers_data,
            'login_logs': login_logs,
            'stock_alerts': stock_alerts,
            'inventory_analytics': inventory_analytics,
            'audit_logs': audit_logs,
            'product_creation_history': product_creation_history,
            'categories': categories,
            'whats_going_on': whats_going_on,
            'predictive_restocking': predictive_restocking,
            'pending_delete_requests': pending_deletes
        }), 200

    return jsonify({'error': 'Unauthorized'}), 401

@auth_bp.route('/reset-user-password', methods=['POST'])
def reset_user_password():
    data = request.get_json()
    username = data.get('username')
    new_password = data.get('new_password')
    user = User.query.filter_by(username=username).first()
    if user:
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        print(f"Reset password for {username}. New hash: {user.password_hash}")
        return jsonify({"success": True, "message": "Password reset."})
    return jsonify({"success": False, "message": "User not found."}), 404