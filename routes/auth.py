from flask import Blueprint, request, jsonify, current_app # type: ignore
from flask_jwt_extended import ( # type: ignore
    create_access_token, jwt_required, get_jwt_identity
)
from flask_limiter import Limiter # type: ignore
from flask_limiter.util import get_remote_address # type: ignore
from datetime import datetime, timedelta
import re, random, string, logging
from app.models import db, Admin, Worker, PasswordResetCode, MFACode
from app.utils import send_email, send_sms_africastalking

auth_bp = Blueprint('auth', __name__)
limiter = Limiter(key_func=get_remote_address)

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
PHONE_REGEX = re.compile(r"^\+?\d{10,15}$")

def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

def validate_email(email):
    return EMAIL_REGEX.match(email)

def validate_phone(phone):
    return PHONE_REGEX.match(phone)

@auth_bp.route('/api/auth/signup', methods=['POST'])
@limiter.limit("5/minute")
def signup():
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    phone = data.get('phone', '').strip()

    if not username or not email or not password:
        return jsonify({"success": False, "message": "Missing required fields."}), 400
    if not validate_email(email):
        return jsonify({"success": False, "message": "Invalid email format."}), 400
    if phone and not validate_phone(phone):
        return jsonify({"success": False, "message": "Invalid phone number."}), 400

    if Worker.query.filter((Worker.username == username)|(Worker.email == email)).first():
        return jsonify({"success": False, "message": "Username or email already exists."}), 409

    worker = Worker(username=username, email=email, phone=phone)
    worker.set_password(password)
    db.session.add(worker)
    db.session.commit()
    return jsonify({"success": True, "message": "Worker registered successfully."})

@auth_bp.route('/api/auth/login', methods=['POST'])
@limiter.limit("10/minute")
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    access_code = data.get('accessCode', '').strip()

    user = None
    user_type = None

    if access_code:
        user = Admin.query.filter_by(username=username).first()
        user_type = 'admin'
        if not user or not user.check_password(password) or access_code != current_app.config.get("ADMIN_ACCESS_CODE"):
            return jsonify({"success": False, "message": "Invalid admin credentials."}), 401
    else:
        user = Worker.query.filter_by(username=username).first()
        user_type = 'worker'
        if not user or not user.check_password(password):
            return jsonify({"success": False, "message": "Invalid worker credentials."}), 401

    mfa_code = generate_code()
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    mfa = MFACode(user_type=user_type, user_id=user.id, code=mfa_code, expires_at=expires_at)
    db.session.add(mfa)
    db.session.commit()

    try:
        if user_type == 'admin':
            send_sms_africastalking(user.phone, f"Your admin login code: {mfa_code}")
        else:
            send_email(user.email, "Your login code", f"Your worker login code: {mfa_code}")
    except Exception as e:
        logging.error(f"Failed to send MFA code: {e}")

    return jsonify({"success": True, "message": "MFA code sent.", "user_type": user_type, "user_id": user.id})

@auth_bp.route('/api/auth/verify-mfa', methods=['POST'])
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

    identity = {"user_type": user_type, "user_id": user_id}
    access_token = create_access_token(identity=identity)
    return jsonify({"success": True, "access_token": access_token})

@auth_bp.route('/api/auth/forgot-code', methods=['POST'])
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

@auth_bp.route('/api/auth/reset-password', methods=['POST'])
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

from functools import wraps
from flask import request, jsonify # type: ignore

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Example: check for a token or session here
        # if not authenticated:
        #     return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function