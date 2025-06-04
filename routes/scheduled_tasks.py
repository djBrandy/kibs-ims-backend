from flask import Blueprint
from app.models import db, PendingDelete, User, AuditLog
from datetime import datetime
import traceback

scheduled_tasks_bp = Blueprint('scheduled_tasks', __name__, url_prefix='/api/scheduled-tasks')

@scheduled_tasks_bp.route('/cleanup-pending-deletes', methods=['POST'])
def cleanup_pending_deletes():
    """
    Process pending deletes that have reached their expiry date
    This endpoint should be called by a scheduled task/cron job
    """
    try:
        # Find all pending deletes that have expired
        now = datetime.utcnow()
        expired_deletes = PendingDelete.query.filter(
            PendingDelete.expiry_date <= now,
            PendingDelete.status == 'pending'
        ).all()
        
        deleted_count = 0
        
        for pending in expired_deletes:
            if pending.worker_id:
                # Get the worker
                worker = User.query.get(pending.worker_id)
                
                if worker:
                    # Create audit log
                    log_entry = AuditLog(
                        product_id=1,  # Placeholder
                        user_id=None,  # System action
                        action_type='auto_delete_worker',
                        previous_value=worker.username,
                        new_value='deleted',
                        notes=f"System automatically deleted worker {worker.id} ({worker.username}) after 30-day pending period"
                    )
                    db.session.add(log_entry)
                    
                    # Delete the worker
                    db.session.delete(worker)
                    
                    # Update pending delete status
                    pending.status = 'completed'
                    deleted_count += 1
        
        db.session.commit()
        
        return {
            'success': True,
            'message': f'Processed {len(expired_deletes)} pending deletes, deleted {deleted_count} workers'
        }, 200
        
    except Exception as e:
        db.session.rollback()
        error_details = traceback.format_exc()
        print(f"Error in cleanup_pending_deletes: {str(e)}")
        print(f"Traceback: {error_details}")
        return {'error': str(e)}, 500

@scheduled_tasks_bp.route('/check-pending-deletes', methods=['GET'])
def check_pending_deletes():
    """Get information about pending deletes"""
    try:
        pending_deletes = PendingDelete.query.filter_by(status='pending').all()
        
        result = []
        for pending in pending_deletes:
            days_remaining = (pending.expiry_date - datetime.utcnow()).days if pending.expiry_date else None
            
            item = pending.to_dict()
            item['days_remaining'] = days_remaining
            result.append(item)
            
        return {'pending_deletes': result}, 200
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error in check_pending_deletes: {str(e)}")
        print(f"Traceback: {error_details}")
        return {'error': str(e)}, 500