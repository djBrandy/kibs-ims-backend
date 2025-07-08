from flask import Blueprint, request, jsonify, session
from app.database import db
from app.models import Suggestion
from routes.auth import login_required
import traceback

suggestions_bp = Blueprint('suggestions', __name__, url_prefix='/api/suggestions')

@suggestions_bp.route('/', methods=['GET'])
@login_required
def get_suggestions():
    """Get suggestions - admins see all, workers see only their own"""
    try:
        user_role = session.get('role', 'worker')
        user_id = session.get('user_id')
        
        if user_role == 'admin':
            # Admins can see all suggestions
            suggestions = Suggestion.query.order_by(Suggestion.created_at.desc()).all()
        else:
            # Workers can only see their own suggestions
            suggestions = Suggestion.query.filter_by(submitted_by=user_id).order_by(Suggestion.created_at.desc()).all()
        
        return jsonify([suggestion.to_dict() for suggestion in suggestions]), 200
    except Exception as e:
        print(f"Error fetching suggestions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@suggestions_bp.route('/', methods=['POST'])
@login_required
def create_suggestion():
    """Create a new suggestion"""
    try:
        data = request.get_json()
        
        suggestion = Suggestion(
            title=data.get('title'),
            description=data.get('description'),
            category=data.get('category', 'general'),
            priority=data.get('priority', 'medium'),
            submitted_by=session.get('user_id')
        )
        
        db.session.add(suggestion)
        db.session.commit()
        
        return jsonify(suggestion.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error creating suggestion: {str(e)}")
        return jsonify({'error': str(e)}), 500

@suggestions_bp.route('/<int:suggestion_id>', methods=['PUT'])
@login_required
def update_suggestion(suggestion_id):
    """Update suggestion - admins can update status/notes, users can update their own"""
    try:
        suggestion = Suggestion.query.get_or_404(suggestion_id)
        data = request.get_json()
        user_role = session.get('role', 'worker')
        user_id = session.get('user_id')
        
        # Check permissions
        if user_role != 'admin' and suggestion.submitted_by != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if user_role == 'admin':
            # Admins can update status and add notes
            if 'status' in data:
                suggestion.status = data['status']
            if 'admin_notes' in data:
                suggestion.admin_notes = data['admin_notes']
            if 'reviewed_by' not in data:
                suggestion.reviewed_by = user_id
        else:
            # Users can only update their own pending suggestions
            if suggestion.status != 'pending':
                return jsonify({'error': 'Cannot edit reviewed suggestions'}), 400
            
            if 'title' in data:
                suggestion.title = data['title']
            if 'description' in data:
                suggestion.description = data['description']
            if 'category' in data:
                suggestion.category = data['category']
            if 'priority' in data:
                suggestion.priority = data['priority']
        
        db.session.commit()
        return jsonify(suggestion.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating suggestion: {str(e)}")
        return jsonify({'error': str(e)}), 500

@suggestions_bp.route('/<int:suggestion_id>', methods=['DELETE'])
@login_required
def delete_suggestion(suggestion_id):
    """Delete suggestion - only by owner or admin"""
    try:
        suggestion = Suggestion.query.get_or_404(suggestion_id)
        user_role = session.get('role', 'worker')
        user_id = session.get('user_id')
        
        # Check permissions
        if user_role != 'admin' and suggestion.submitted_by != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        db.session.delete(suggestion)
        db.session.commit()
        return jsonify({'message': 'Suggestion deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting suggestion: {str(e)}")
        return jsonify({'error': str(e)}), 500

@suggestions_bp.route('/stats', methods=['GET'])
@login_required
def get_suggestion_stats():
    """Get suggestion statistics - admin only"""
    try:
        user_role = session.get('role', 'worker')
        if user_role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        total = Suggestion.query.count()
        pending = Suggestion.query.filter_by(status='pending').count()
        reviewed = Suggestion.query.filter_by(status='reviewed').count()
        implemented = Suggestion.query.filter_by(status='implemented').count()
        rejected = Suggestion.query.filter_by(status='rejected').count()
        
        return jsonify({
            'total': total,
            'pending': pending,
            'reviewed': reviewed,
            'implemented': implemented,
            'rejected': rejected
        }), 200
    except Exception as e:
        print(f"Error fetching suggestion stats: {str(e)}")
        return jsonify({'error': str(e)}), 500