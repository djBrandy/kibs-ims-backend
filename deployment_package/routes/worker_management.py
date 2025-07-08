from flask import Blueprint, request, jsonify, session
from app.models import db, User, AuditLog, PendingDelete
from routes.auth import admin_required, login_required
from datetime import datetime, timedelta
import json

worker_bp = Blueprint('worker', __name__, url_prefix='/api/workers')

@worker_bp.route('/', methods=['GET'])
@admin_required
def get_workers():
    """Get all workers with their activity data"""
    workers = User.query.filter_by(role='worker').all()
    
    workers_data = []
    for worker in workers:
        # Count audits by this worker
        audit_count = AuditLog.query.filter_by(user_id=worker.id).count()
        
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
            'created_at': worker.created_at.isoformat() if worker.created_at else None,
            'last_login': worker.last_login.isoformat() if worker.last_login else None,
            'last_activity': worker.last_activity.isoformat() if worker.last_activity else None,
            'audit_count': audit_count,
            'permissions': permissions
        })
    
    return jsonify(workers_data), 200

@worker_bp.route('/<int:worker_id>/permissions', methods=['PUT'])
@admin_required
def update_permissions(worker_id):
    """Update a worker's permissions"""
    worker = User.query.get_or_404(worker_id)
    
    if worker.role != 'worker':
        return jsonify({'error': 'Can only modify worker permissions'}), 400
    
    data = request.get_json()
    permissions = data.get('permissions', {})
    
    # Store permissions as JSON string
    worker.permissions = json.dumps(permissions)
    
    # Log the change
    admin_id = session.get('user_id')
    log_entry = AuditLog(
        product_id=1,  # Placeholder
        user_id=admin_id,
        action_type='update_permissions',
        previous_value=worker.permissions,
        new_value=json.dumps(permissions),
        notes=f"Admin {admin_id} updated permissions for worker {worker_id}"
    )
    
    db.session.add(log_entry)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Permissions updated'}), 200

@worker_bp.route('/<int:worker_id>/ban', methods=['PUT'])
@admin_required
def ban_worker(worker_id):
    """Ban a worker"""
    worker = User.query.get_or_404(worker_id)
    
    if worker.role != 'worker':
        return jsonify({'error': 'Can only ban workers'}), 400
    
    data = request.get_json()
    reason = data.get('reason', 'No reason provided')
    
    worker.is_banned = True
    worker.ban_reason = reason
    worker.is_active = False
    
    # Log the ban
    admin_id = session.get('user_id')
    log_entry = AuditLog(
        product_id=1,  # Placeholder
        user_id=admin_id,
        action_type='ban_worker',
        previous_value='active',
        new_value='banned',
        notes=f"Admin {admin_id} banned worker {worker_id}. Reason: {reason}"
    )
    
    db.session.add(log_entry)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Worker banned'}), 200

@worker_bp.route('/<int:worker_id>/unban', methods=['PUT'])
@admin_required
def unban_worker(worker_id):
    """Unban a worker"""
    worker = User.query.get_or_404(worker_id)
    
    if worker.role != 'worker':
        return jsonify({'error': 'Can only unban workers'}), 400
    
    worker.is_banned = False
    worker.ban_reason = None
    worker.is_active = True
    
    # Log the unban
    admin_id = session.get('user_id')
    log_entry = AuditLog(
        product_id=1,  # Placeholder
        user_id=admin_id,
        action_type='unban_worker',
        previous_value='banned',
        new_value='active',
        notes=f"Admin {admin_id} unbanned worker {worker_id}"
    )
    
    db.session.add(log_entry)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Worker unbanned'}), 200

@worker_bp.route('/<int:worker_id>/delete', methods=['DELETE'])
@admin_required
def delete_worker(worker_id):
    """Delete a worker account"""
    worker = User.query.get_or_404(worker_id)
    
    if worker.role != 'worker':
        return jsonify({'error': 'Can only delete worker accounts'}), 400
    
    # Log the deletion
    admin_id = session.get('user_id')
    log_entry = AuditLog(
        product_id=1,  # Placeholder
        user_id=admin_id,
        action_type='delete_worker',
        previous_value=worker.username,
        new_value='pending_delete',
        notes=f"Admin {admin_id} marked worker {worker_id} ({worker.username}) for deletion"
    )
    
    db.session.add(log_entry)
    
    # Create pending delete entry instead of deleting immediately
    from datetime import datetime, timedelta
    from app.models import PendingDelete
    
    # Store worker data in pending_deletes table
    pending_delete = PendingDelete(
        worker_id=worker.id,
        timestamp=datetime.utcnow(),
        status='pending',
        reason=request.json.get('reason', 'No reason provided')
    )
    
    # Set expiry date to 30 days from now
    pending_delete.expiry_date = datetime.utcnow() + timedelta(days=30)
    
    # Deactivate the worker account but don't delete it yet
    worker.is_active = False
    worker.is_banned = True
    worker.ban_reason = "Pending deletion"
    
    db.session.add(pending_delete)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Worker marked for deletion and will be automatically deleted after 30 days'
    }), 200

@worker_bp.route('/activity', methods=['POST'])
@login_required
def update_activity():
    """Update a user's last activity time"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.last_activity = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True}), 200