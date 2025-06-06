from flask import Blueprint, request, jsonify
from app.models import Room, Product, DeletedItem, PendingDelete
from app import db
from datetime import datetime, timedelta
from flask_cors import CORS  # type: ignore

rooms_bp = Blueprint('rooms', __name__)
CORS(rooms_bp)

# --- Custom Error Handlers ---
@rooms_bp.errorhandler(404)
def handle_404(error):
    return jsonify({'error': 'Resource not found'}), 404

@rooms_bp.errorhandler(405)
def handle_405(error):
    return jsonify({'error': 'Method not allowed'}), 405

@rooms_bp.errorhandler(500)
def handle_500(error):
    return jsonify({'error': 'Server error'}), 500

# --- API Endpoints ---

@rooms_bp.route('/api/rooms', methods=['GET', 'OPTIONS'])
def get_rooms():
    """Get all rooms"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET')
        return response, 200
        
    try:
        # Get all rooms
        rooms = Room.query.all()
        
        # Get room IDs that are in pending_delete
        pending_delete_room_ids = [pd.room_id for pd in PendingDelete.query.filter(
            PendingDelete.room_id.isnot(None),
            PendingDelete.status == 'pending'
        ).all()]
        
        # Filter out rooms that are in pending_delete
        rooms_data = [room.to_dict() for room in rooms 
                     if room.id not in pending_delete_room_ids]
        
        response = jsonify(rooms_data)
    except Exception as e:
        print(f"Error fetching rooms: {str(e)}")
        response = jsonify([])  # Return empty array on error
        
    # Always add CORS headers
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET')
    return response, 200

@rooms_bp.route('/api/rooms/<int:room_id>', methods=['GET', 'OPTIONS'])
def get_room(room_id):
    """Get a specific room by ID"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET')
        return response, 200
        
    room = Room.query.get_or_404(room_id)
    response = jsonify(room.to_dict())
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET')
    return response, 200

@rooms_bp.route('/api/rooms', methods=['POST', 'OPTIONS'])
def create_room():
    """Create a new room"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response, 200

    data = request.get_json()

    if not data or 'name' not in data:
        return jsonify({'error': 'Room name is required'}), 400

    # Check if room with the same name already exists
    existing_room = Room.query.filter_by(name=data['name']).first()
    if existing_room:
        return jsonify({'error': 'Room with this name already exists'}), 409

    new_room = Room(
        name=data['name'],
        description=data.get('description', '')
    )

    db.session.add(new_room)
    db.session.commit()

    return jsonify(new_room.to_dict()), 201

@rooms_bp.route('/api/rooms/<int:room_id>', methods=['PUT', 'OPTIONS'])
def update_room(room_id):
    """Update a room"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'PUT')
        return response, 200

    room = Room.query.get_or_404(room_id)
    data = request.get_json()

    if 'name' in data:
        # Check if another room with this name exists
        existing_room = Room.query.filter(Room.name == data['name'], Room.id != room_id).first()
        if existing_room:
            return jsonify({'error': 'Another room with this name already exists'}), 409
        room.name = data['name']

    if 'description' in data:
        room.description = data['description']

    db.session.commit()
    return jsonify(room.to_dict()), 200

@rooms_bp.route('/api/rooms/<int:room_id>', methods=['DELETE', 'OPTIONS'])
def delete_room(room_id):
    """Add room and its products to pending_delete without removing them from their tables"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        return response, 200

    try:
        # Use get instead of get_or_404 to handle missing rooms gracefully
        room = Room.query.get(room_id)
        if not room:
            response = jsonify({'error': f'Room with ID {room_id} not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404

        # Check if room is already in pending_delete
        existing_pending = PendingDelete.query.filter_by(room_id=room_id, status='pending').first()
        if existing_pending:
            response = jsonify({'error': 'This room is already pending deletion'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 409

        # Get user_id from request
        user_data = request.get_json() or {}
        worker_id = user_data.get('user_id', 1)  # Default to 1 if not provided
        current_time = datetime.now()
        
        # First, add all products in the room to pending_delete
        products_added = 0
        
        # Process products in the room
        if room.products:
            for product in room.products:
                # Check if product is already in pending_delete
                if not PendingDelete.query.filter_by(product_id=product.id, status='pending').first():
                    product_pending = PendingDelete(
                        product_id=product.id,
                        room_id=None,  # Don't set room_id for product entries
                        timestamp=current_time,
                        status='pending',
                        reason=f"Product deletion requested as part of room deletion: {room.name}",
                        worker_id=worker_id
                    )
                    db.session.add(product_pending)
                    products_added += 1
                    # Commit each product individually to avoid transaction issues
                    db.session.commit()
        
        # Then add the room itself to pending_delete
        room_pending = PendingDelete(
            product_id=None,  # Explicitly set product_id to None for room deletions
            room_id=room_id,  # Store room ID in room_id field
            timestamp=current_time,
            status='pending',
            reason=f"Room deletion requested: {room.name}",
            worker_id=worker_id
        )
        
        db.session.add(room_pending)
        db.session.commit()

        response = jsonify({
            'message': f'Room and {products_added} products marked for deletion and awaiting approval'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        db.session.rollback()
        print(f"Error processing room deletion request: {str(e)}")
        response = jsonify({'error': f'Failed to process deletion request: {str(e)}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@rooms_bp.route('/api/deleted-items', methods=['GET'])
def get_deleted_items():
    """Get all deleted items"""
    deleted_items = DeletedItem.query.all()
    return jsonify([item.to_dict() for item in deleted_items]), 200

@rooms_bp.route('/api/deleted-items/<int:item_id>/restore', methods=['POST'])
def restore_deleted_item(item_id):
    """Restore a deleted item"""
    deleted_item = DeletedItem.query.get_or_404(item_id)
    
    if deleted_item.item_type == 'room':
        # Restore room
        room_data = deleted_item.data
        new_room = Room(
            name=room_data['name'],
            description=room_data.get('description', '')
        )
        db.session.add(new_room)
    
    db.session.delete(deleted_item)
    db.session.commit()

    return jsonify({'message': f'{deleted_item.item_type.capitalize()} restored successfully'}), 200