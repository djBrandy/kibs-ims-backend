from flask import Blueprint, jsonify, request
from app.models import db, User, LoginLog, SystemMetrics, AdminPanel, PendingDelete
from routes.middleware import admin_required, token_required
from datetime import datetime, timedelta
from sqlalchemy import func
import platform
import psutil
import time

admin_panel_bp = Blueprint('admin_panel', __name__, url_prefix='/api/admin-panel')

@admin_panel_bp.route('/', methods=['GET'])
@token_required
def get_admin_panel_data():
    """Get admin panel data including metrics and user activity"""
    try:
        # Get active users (users who logged in within the last 24 hours)
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        active_users = User.query.filter(User.last_activity >= one_day_ago).count()
        
        # Get total logins
        total_logins = LoginLog.query.count()
        
        # Get new users today
        today = datetime.utcnow().date()
        new_users_today = User.query.filter(
            func.date(User.created_at) == today
        ).count()
        
        # Get system uptime
        uptime = "99.9%"  # Default value
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_days = uptime_seconds / (60 * 60 * 24)
            uptime = f"{uptime_days:.1f} days"
        except:
            pass
        
        # Get all workers
        workers = User.query.filter_by(role='worker').all()
        workers_data = [
            {
                'id': worker.id,
                'username': worker.username,
                'email': worker.email,
                'is_active': worker.is_active,
                'last_login': worker.last_login.isoformat() if worker.last_login else None,
                'last_activity': worker.last_activity.isoformat() if worker.last_activity else None,
                'created_at': worker.created_at.isoformat() if worker.created_at else None
            }
            for worker in workers
        ]
        
        # Get login logs
        login_logs = LoginLog.query.order_by(LoginLog.timestamp.desc()).limit(50).all()
        login_logs_data = [log.to_dict() for log in login_logs]
        
        # Update or create AdminPanel record
        admin_panel = AdminPanel.query.first()
        if not admin_panel:
            admin_panel = AdminPanel(
                active_users_count=active_users,
                total_logins=total_logins,
                new_users_today=new_users_today,
                system_uptime=uptime
            )
            db.session.add(admin_panel)
        else:
            admin_panel.active_users_count = active_users
            admin_panel.total_logins = total_logins
            admin_panel.new_users_today = new_users_today
            admin_panel.system_uptime = uptime
            admin_panel.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        # Return all data
        return jsonify({
            'metrics': {
                'active_users': active_users,
                'total_logins': total_logins,
                'new_users_today': new_users_today,
                'system_uptime': uptime
            },
            'workers': workers_data,
            'login_logs': login_logs_data,
            'last_updated': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_panel_bp.route('/log-login', methods=['POST'])
@token_required
def log_login():
    """Log a user login"""
    data = request.json
    user_id = data.get('user_id')
    status = data.get('status', 'success')
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    try:
        login_log = LoginLog(
            user_id=user_id,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(login_log)
        db.session.commit()
        
        return jsonify({'success': True, 'log_id': login_log.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_panel_bp.route('/mark-worker-delete', methods=['POST'])
@admin_required
def mark_worker_for_deletion():
    """Mark a worker for deletion (move to pending_delete)"""
    data = request.json
    worker_id = data.get('worker_id')
    reason = data.get('reason', 'Admin requested deletion')
    
    if not worker_id:
        return jsonify({'error': 'Worker ID is required'}), 400
    
    try:
        # Find the worker
        worker = User.query.get(worker_id)
        if not worker:
            return jsonify({'error': 'Worker not found'}), 404
        
        # Create pending delete entry
        pending_delete = PendingDelete(
            worker_id=worker_id,
            timestamp=datetime.utcnow(),
            status='pending',
            reason=reason
        )
        
        db.session.add(pending_delete)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Worker {worker.username} marked for deletion',
            'pending_delete_id': pending_delete.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_panel_bp.route('/system-metrics', methods=['GET'])
@admin_required
def get_system_metrics():
    """Get detailed system metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # System info
        system_info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'hostname': platform.node()
        }
        
        # Save metrics to database
        for name, value in {
            'cpu_usage': f"{cpu_percent}%",
            'memory_usage': f"{memory_percent}%",
            'disk_usage': f"{disk_percent}%"
        }.items():
            metric = SystemMetrics(
                metric_name=name,
                metric_value=value
            )
            db.session.add(metric)
        
        db.session.commit()
        
        return jsonify({
            'cpu_usage': cpu_percent,
            'memory_usage': memory_percent,
            'disk_usage': disk_percent,
            'system_info': system_info
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500