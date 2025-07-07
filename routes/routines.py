from flask import Blueprint, request, jsonify
from app.database import db
from app.models import Routine, RoutineCompletion
from datetime import datetime, date, time
from routes.auth import login_required
import traceback

routines_bp = Blueprint('routines', __name__, url_prefix='/api/routines')

@routines_bp.route('/', methods=['GET'])
@login_required
def get_routines():
    """Get all active routines"""
    try:
        routines = Routine.query.filter_by(is_active=True).all()
        return jsonify([routine.to_dict() for routine in routines]), 200
    except Exception as e:
        print(f"Error fetching routines: {str(e)}")
        return jsonify({'error': str(e)}), 500

@routines_bp.route('/', methods=['POST'])
@login_required
def create_routine():
    """Create a new routine"""
    try:
        data = request.get_json()
        
        # Parse time string (HH:MM format)
        time_str = data.get('scheduled_time')
        if not time_str:
            return jsonify({'error': 'Scheduled time is required'}), 400
        
        try:
            hour, minute = map(int, time_str.split(':'))
            scheduled_time = time(hour, minute)
        except ValueError:
            return jsonify({'error': 'Invalid time format. Use HH:MM'}), 400
        
        routine = Routine(
            title=data.get('title'),
            description=data.get('description', ''),
            scheduled_time=scheduled_time,
            frequency=data.get('frequency', 'daily'),
            created_by=data.get('created_by')
        )
        
        db.session.add(routine)
        db.session.commit()
        
        return jsonify(routine.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error creating routine: {str(e)}")
        return jsonify({'error': str(e)}), 500

@routines_bp.route('/<int:routine_id>', methods=['PUT'])
@login_required
def update_routine(routine_id):
    """Update a routine"""
    try:
        routine = Routine.query.get_or_404(routine_id)
        data = request.get_json()
        
        if 'title' in data:
            routine.title = data['title']
        if 'description' in data:
            routine.description = data['description']
        if 'scheduled_time' in data:
            time_str = data['scheduled_time']
            hour, minute = map(int, time_str.split(':'))
            routine.scheduled_time = time(hour, minute)
        if 'frequency' in data:
            routine.frequency = data['frequency']
        if 'is_active' in data:
            routine.is_active = data['is_active']
        
        db.session.commit()
        return jsonify(routine.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating routine: {str(e)}")
        return jsonify({'error': str(e)}), 500

@routines_bp.route('/<int:routine_id>', methods=['DELETE'])
@login_required
def delete_routine(routine_id):
    """Delete a routine"""
    try:
        routine = Routine.query.get_or_404(routine_id)
        routine.is_active = False  # Soft delete
        db.session.commit()
        return jsonify({'message': 'Routine deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting routine: {str(e)}")
        return jsonify({'error': str(e)}), 500

@routines_bp.route('/today', methods=['GET'])
@login_required
def get_today_routines():
    """Get today's routines with completion status"""
    try:
        today = date.today()
        routines = Routine.query.filter_by(is_active=True).all()
        
        result = []
        for routine in routines:
            # Check if routine was completed today
            completion = RoutineCompletion.query.filter_by(
                routine_id=routine.id,
                completion_date=today
            ).first()
            
            routine_data = routine.to_dict()
            routine_data['completion'] = completion.to_dict() if completion else None
            routine_data['is_completed_today'] = completion.is_completed if completion else False
            
            result.append(routine_data)
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Error fetching today's routines: {str(e)}")
        return jsonify({'error': str(e)}), 500

@routines_bp.route('/<int:routine_id>/complete', methods=['POST'])
@login_required
def complete_routine(routine_id):
    """Mark a routine as completed for today"""
    try:
        routine = Routine.query.get_or_404(routine_id)
        data = request.get_json()
        today = date.today()
        
        # Check if already completed today
        completion = RoutineCompletion.query.filter_by(
            routine_id=routine_id,
            completion_date=today
        ).first()
        
        if completion:
            # Update existing completion
            completion.is_completed = True
            completion.completed_at = datetime.utcnow()
            completion.completed_by = data.get('completed_by')
            completion.notes = data.get('notes', '')
        else:
            # Create new completion record
            completion = RoutineCompletion(
                routine_id=routine_id,
                completion_date=today,
                completed_at=datetime.utcnow(),
                completed_by=data.get('completed_by'),
                is_completed=True,
                notes=data.get('notes', '')
            )
            db.session.add(completion)
        
        db.session.commit()
        return jsonify(completion.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error completing routine: {str(e)}")
        return jsonify({'error': str(e)}), 500

@routines_bp.route('/overdue', methods=['GET'])
@login_required
def get_overdue_routines():
    """Get routines that are overdue (not completed and past reminder time)"""
    try:
        today = date.today()
        current_time = datetime.now().time()
        
        routines = Routine.query.filter_by(is_active=True).all()
        overdue = []
        
        for routine in routines:
            # Check if routine time has passed today
            if current_time > routine.scheduled_time:
                # Check if not completed today
                completion = RoutineCompletion.query.filter_by(
                    routine_id=routine.id,
                    completion_date=today
                ).first()
                
                if not completion or not completion.is_completed:
                    routine_data = routine.to_dict()
                    routine_data['hours_overdue'] = (
                        datetime.combine(today, current_time) - 
                        datetime.combine(today, routine.scheduled_time)
                    ).total_seconds() / 3600
                    overdue.append(routine_data)
        
        return jsonify(overdue), 200
    except Exception as e:
        print(f"Error fetching overdue routines: {str(e)}")
        return jsonify({'error': str(e)}), 500