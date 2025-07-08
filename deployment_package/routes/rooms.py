from flask import Blueprint, request, jsonify
from app.models import Room, Product, DeletedItem, PendingDelete
from app.database import db
from datetime import datetime, timedelta

rooms_bp = Blueprint('rooms', __name__)

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
        return jsonify({}), 200
        
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
        
        return jsonify(rooms_data), 200
    except Exception as e:
        print(f"Error fetching rooms: {str(e)}")
        return jsonify([]), 200

@rooms_bp.route('/api/rooms/<int:room_id>', methods=['GET', 'OPTIONS'])
def get_room(room_id):
    """Get a specific room by ID"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    room = Room.query.get_or_404(room_id)
    return jsonify(room.to_dict()), 200

@rooms_bp.route('/api/rooms', methods=['POST', 'OPTIONS'])
def create_room():
    """Create a new room"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

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
        return jsonify({}), 200

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
        return jsonify({}), 200

    try:
        # Use get instead of get_or_404 to handle missing rooms gracefully
        room = Room.query.get(room_id)
        if not room:
            return jsonify({'error': f'Room with ID {room_id} not found'}), 404

        # Check if room is already in pending_delete
        existing_pending = PendingDelete.query.filter_by(room_id=room_id, status='pending').first()
        if existing_pending:
            return jsonify({'error': 'This room is already pending deletion'}), 409

        # Get user_id from request
        user_data = request.get_json() or {}
        worker_id = user_data.get('user_id', 1)  # Default to 1 if not provided
        current_time = datetime.now()
        products_added = 0
        
        # First process all products in the room if any
        if room.products:
            for product in room.products:
                # Skip products already in pending_delete
                if PendingDelete.query.filter_by(product_id=product.id, status='pending').first():
                    continue
                    
                # Add product to pending_delete
                product_pending = PendingDelete(
                    product_id=product.id,
                    room_id=room_id,
                    timestamp=current_time,
                    status='pending',
                    reason=f"Product deletion requested as part of room deletion: {room.name}",
                    worker_id=worker_id
                )
                db.session.add(product_pending)
                products_added += 1
        
        # Then add the room itself to pending_delete
        room_pending = PendingDelete(
            product_id=None,
            room_id=room_id,
            timestamp=current_time,
            status='pending',
            reason=f"Room deletion requested: {room.name}",
            worker_id=worker_id
        )
        db.session.add(room_pending)
        
        # Commit everything in a single transaction
        db.session.commit()

        return jsonify({
            'message': f'Room and {products_added} products marked for deletion and awaiting approval'
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error processing room deletion request: {str(e)}")
        return jsonify({'error': f'Failed to process deletion request: {str(e)}'}), 500

@rooms_bp.route('/api/deleted-items', methods=['GET', 'OPTIONS'])
def get_deleted_items():
    """Get all deleted items including pending deletes"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        # Get items from DeletedItem table
        deleted_items = [item.to_dict() for item in DeletedItem.query.all()]
        
        # Get items from PendingDelete table
        pending_deletes = PendingDelete.query.filter_by(status='pending').all()
        
        pending_items = []
        for pd in pending_deletes:
            item_data = {}
            
            # Handle product deletions
            if pd.product_id:
                product = Product.query.get(pd.product_id)
                if product:
                    item_data = {
                        'id': f"pending_{pd.id}",
                        'original_id': pd.product_id,
                        'item_type': 'product',
                        'data': product.to_dict(),
                        'deleted_at': pd.timestamp.isoformat() if pd.timestamp else datetime.now().isoformat(),
                        'expiry_date': ((pd.timestamp if pd.timestamp else datetime.now()) + timedelta(days=30)).isoformat(),
                        'days_remaining': 30,
                        'pending': True,
                        'reason': pd.reason
                    }
                    pending_items.append(item_data)
            
            # Handle room deletions
            elif pd.room_id:
                room = Room.query.get(pd.room_id)
                if room:
                    item_data = {
                        'id': f"pending_{pd.id}",
                        'original_id': pd.room_id,
                        'item_type': 'room',
                        'data': room.to_dict(),
                        'deleted_at': pd.timestamp.isoformat() if pd.timestamp else datetime.now().isoformat(),
                        'expiry_date': ((pd.timestamp if pd.timestamp else datetime.now()) + timedelta(days=30)).isoformat(),
                        'days_remaining': 30,
                        'pending': True,
                        'reason': pd.reason
                    }
                    pending_items.append(item_data)
        
        # Combine both lists
        all_items = deleted_items + pending_items
        
        return jsonify(all_items), 200
    except Exception as e:
        print(f"Error getting deleted items: {str(e)}")
        return jsonify({'error': f'Failed to get deleted items: {str(e)}'}), 500

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

@rooms_bp.route('/api/pending-deletes/<int:item_id>/cancel', methods=['POST', 'OPTIONS'])
def cancel_pending_delete(item_id):
    """Cancel a pending delete"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        pending_delete = PendingDelete.query.get_or_404(item_id)
        
        # Delete the pending delete entry
        db.session.delete(pending_delete)
        db.session.commit()
        
        # Determine the type of item that was restored
        item_type = "unknown"
        if pending_delete.product_id:
            item_type = "product"
        elif pending_delete.room_id:
            item_type = "room"
        
        return jsonify({'message': f'{item_type.capitalize()} deletion cancelled successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error cancelling pending delete: {str(e)}")
        return jsonify({'error': f'Failed to cancel pending delete: {str(e)}'}), 500