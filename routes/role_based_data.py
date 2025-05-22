from flask import Blueprint, jsonify, session
from app.models import db, Product, Supplier, Worker, AuditLog, InventoryAnalytics, AlertNotification, User
from routes.auth import login_required, debug_session
from datetime import datetime, timedelta
from sqlalchemy import func

role_data_bp = Blueprint('role_data', __name__, url_prefix='/api/role-data')

@role_data_bp.route('/', methods=['GET'])
@login_required
def get_role_based_data():
    """
    Returns data based on the user's role.
    Workers see: products in stock, supplier info
    Admins see: all info including workers list, login logs, stock alerts, inventory analytics, audit logs, product creation history
    """
    from flask import request
    
    # Debug session info
    debug_session()
    
    # Get role from query parameter (for debugging) or session
    user_role = request.args.get('role') or session.get('role', 'worker')
    user_id = session.get('user_id')
    
    # Force admin role if specified in query parameter
    if request.args.get('role') == 'admin':
        user_role = 'admin'
        print("Forcing admin role from query parameter")
    
    # For debugging: force admin role if username contains 'admin'
    if user_id:
        user = User.query.get(user_id)
        if user and user.username.lower() == 'admin':
            user_role = 'admin'
            # Update session
            session['role'] = 'admin'
            session.modified = True
            print(f"Forced admin role for {user.username}")
    
    print(f"Role-based data using role: {user_role}")
    
    # Base data that all users can see
    data = {
        'role': user_role,
    }
    
    # Worker view: only products in stock and supplier info
    if user_role == 'worker':
        data['products'] = [
            p.to_dict() for p in Product.query.filter(Product.quantity > 0).all()
        ]
        data['suppliers'] = [s.to_dict() for s in Supplier.query.all()]
        
        # Log this access for analytics
        if user_id:
            log_entry = AuditLog(
                product_id=1,  # Placeholder
                user_id=user_id,
                action_type='page_view',
                notes=f"Worker viewed products and suppliers list"
            )
            db.session.add(log_entry)
            db.session.commit()
    
    # Admin view: all information
    elif user_role == 'admin':
        data['products'] = [p.to_dict() for p in Product.query.all()]
        data['suppliers'] = [s.to_dict() for s in Supplier.query.all()]
        
        # Workers list with enhanced data
        workers_data = []
        users = User.query.filter_by(role='worker').all()
        
        for user in users:
            # Count audits by this worker
            audit_count = AuditLog.query.filter_by(user_id=user.id).count()
            
            # Get last activity time
            last_activity = user.last_activity.isoformat() if user.last_activity else None
            
            # Count page views in the last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            page_views = AuditLog.query.filter_by(
                user_id=user.id, 
                action_type='page_view'
            ).filter(
                AuditLog.timestamp >= thirty_days_ago
            ).count()
            
            # Calculate time spent in app (rough estimate based on activity logs)
            time_spent = 0
            if user.last_login and user.last_activity:
                time_spent = (user.last_activity - user.last_login).total_seconds() / 60  # in minutes
            
            workers_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'is_active': user.is_active,
                'is_banned': user.is_banned if hasattr(user, 'is_banned') else False,
                'ban_reason': user.ban_reason if hasattr(user, 'ban_reason') else None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'last_activity': last_activity,
                'audit_count': audit_count,
                'page_views': page_views,
                'time_spent_minutes': round(time_spent, 1),
                'permissions': user.permissions
            })
        
        data['workers'] = workers_data
        
        # Login logs
        login_logs = AuditLog.query.filter_by(action_type='login').order_by(AuditLog.timestamp.desc()).limit(50).all()
        data['login_logs'] = [log.to_dict() for log in login_logs]
        
        # Stock alerts
        stock_alerts = Product.query.filter(Product.quantity <= Product.low_stock_alert).all()
        data['stock_alerts'] = [p.to_dict() for p in stock_alerts]
        
        # Inventory analytics
        inventory_analytics = InventoryAnalytics.query.all()
        data['inventory_analytics'] = [a.to_dict() for a in inventory_analytics]
        
        # Audit logs with enhanced information
        audit_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
        enhanced_logs = []
        
        for log in audit_logs:
            log_dict = log.to_dict()
            
            # Add username if available
            if log.user_id:
                user = User.query.get(log.user_id)
                if user:
                    log_dict['username'] = user.username
                    log_dict['user_role'] = user.role
            
            enhanced_logs.append(log_dict)
        
        data['audit_logs'] = enhanced_logs
        
        # Product creation history (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        product_creation = Product.query.filter(Product.date_of_entry >= thirty_days_ago).all()
        data['product_creation_history'] = [p.to_dict() for p in product_creation]
        
        # Activity summary
        data['activity_summary'] = {
            'total_logins': AuditLog.query.filter_by(action_type='login').count(),
            'total_audits': AuditLog.query.filter_by(action_type='audit').count(),
            'total_products_created': AuditLog.query.filter_by(action_type='create_product').count(),
            'total_products_updated': AuditLog.query.filter_by(action_type='update_product').count(),
            'total_products_deleted': AuditLog.query.filter_by(action_type='delete_product').count(),
        }
    
    return jsonify(data)