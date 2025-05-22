from flask import Blueprint, request, jsonify, session
from app.models import db, User, AuditLog, Product, Category, InventoryAnalytics
from routes.middleware import admin_required, auth_required
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users (admin only)"""
    users = User.query.all()
    return jsonify({
        'success': True,
        'users': [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active,
                'last_login': user.last_login.isoformat() if user.last_login else None
            } for user in users
        ]
    })

@admin_bp.route('/logs', methods=['GET'])
@admin_required
def get_logs():
    """Get audit logs (admin only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'success': True,
        'logs': [log.to_dict() for log in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': logs.page
    })

@admin_bp.route('/analytics', methods=['GET'])
@admin_required
def get_analytics():
    """Get inventory analytics (admin only)"""
    analytics = {
        'total_products': Product.query.count(),
        'out_of_stock': Product.query.filter(Product.quantity == 0).count(),
        'low_stock': Product.query.filter(Product.quantity <= Product.low_stock_alert).count(),
        'categories': Category.query.count(),
        'product_movement': [
            {
                'id': a.id,
                'product_id': a.product_id,
                'product_name': a.product.product_name if a.product else 'Unknown',
                'days_without_movement': a.days_without_movement,
                'is_dead_stock': a.is_dead_stock,
                'is_slow_moving': a.is_slow_moving,
                'is_top_product': a.is_top_product
            }
            for a in InventoryAnalytics.query.all()
        ]
    }
    
    return jsonify({
        'success': True,
        'analytics': analytics
    })

@admin_bp.route('/user/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Update user details (admin only)"""
    user = User.query.get_or_404(user_id)
    data = request.json
    
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    if 'role' in data:
        user.role = data['role']
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    db.session.commit()
    
    # Log the action
    log = AuditLog(
        product_id=1,  # Placeholder
        user_id=session.get('user_id'),
        action_type='user_update',
        notes=f"Updated user {user.username} (ID: {user.id})"
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'User {user.username} updated successfully'
    })

@admin_bp.route('/user/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user (admin only)"""
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        return jsonify({
            'success': False,
            'message': 'Cannot delete admin users'
        }), 403
    
    username = user.username
    db.session.delete(user)
    
    # Log the action
    log = AuditLog(
        product_id=1,  # Placeholder
        user_id=session.get('user_id'),
        action_type='user_delete',
        notes=f"Deleted user {username} (ID: {user_id})"
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'User {username} deleted successfully'
    })