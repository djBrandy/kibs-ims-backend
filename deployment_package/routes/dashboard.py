from flask import Blueprint, jsonify, session # type: ignore
from routes.auth import login_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/', methods=['GET'])
@login_required
def get_dashboard_data():
    from app.database import db
    from app.models import Product, Supplier, User, AuditLog

    user_role = session.get('role', 'worker')

    # Common data for all users
    if user_role == 'worker':
        products = [
            {
                'id': p.id,
                'product_name': p.product_name,
                'quantity': p.quantity,
                'unit_of_measure': p.unit_of_measure,
                'expiration_date': p.expiration_date.isoformat() if p.expiration_date else None
            }
            for p in Product.query.filter(Product.quantity > 0).all()
        ]
        suppliers = [
            {
                'id': s.id,
                'shop_name': s.shop_name,
                'primary_contact': s.primary_contact,
                'phone': s.phone,
                'email': s.email,
                'address': s.address
            }
            for s in Supplier.query.all()
        ]
        return jsonify({
            'role': user_role,
            'products': products,
            'suppliers': suppliers
        }), 200

    elif user_role == 'admin':
        products = [
            {
                'id': p.id,
                'product_name': p.product_name,
                'quantity': p.quantity,
                'unit_of_measure': p.unit_of_measure,
                'expiration_date': p.expiration_date.isoformat() if p.expiration_date else None
            }
            for p in Product.query.all()
        ]
        suppliers = [
            {
                'id': s.id,
                'shop_name': s.shop_name,
                'primary_contact': s.primary_contact,
                'phone': s.phone,
                'email': s.email,
                'address': s.address
            }
            for s in Supplier.query.all()
        ]
        workers = [
            {'id': u.id, 'name': u.username, 'email': u.email, 'role': u.role}
            for u in User.query.filter_by(role='worker').all()
        ]
        login_logs = [
            {
                'user_id': log.user_id,
                'timestamp': log.timestamp.isoformat(),
                'ip': log.ip_address
            }
            for log in AuditLog.query.filter_by(action_type='login').order_by(AuditLog.timestamp.desc()).limit(50)
        ]
        product_creations = [
            {
                'product_id': log.product_id,
                'user_id': log.user_id,
                'timestamp': log.timestamp.isoformat()
            }
            for log in AuditLog.query.filter_by(action_type='create').order_by(AuditLog.timestamp.desc()).limit(50)
        ]
        return jsonify({
            'role': user_role,
            'products': products,
            'suppliers': suppliers,
            'workers': workers,
            'login_logs': login_logs,
            'product_creation_history': product_creations
        }), 200

    else:
        return jsonify({'error': 'Invalid role'}), 403