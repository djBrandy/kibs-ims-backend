from flask import Blueprint, request, jsonify
from app.models import Room, Product, DeletedItem
from app import db
from routes.middleware import admin_required, token_required
import json
from datetime import datetime, timedelta

rooms_bp = Blueprint('rooms', __name__)

@rooms_bp.route('/api/rooms', methods=['GET'])
@token_required
def get_rooms():
    """Get all rooms"""
    rooms = Room.query.all()
    return jsonify([room.to_dict() for room in rooms]), 200

@rooms_bp.route('/api/rooms/<int:room_id>', methods=['GET'])
@token_required
def get_room(room_id):
    """Get a specific room by ID"""
    room = Room.query.get_or_404(room_id)
    return jsonify(room.to_dict()), 200

@rooms_bp.route('/api/rooms', methods=['POST'])
@admin_required
def create_room():
    """Create a new room"""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Room name is required'}), 400
    
    # Check if room with same name already exists
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

@rooms_bp.route('/api/rooms/<int:room_id>', methods=['PUT'])
@admin_required
def update_room(room_id):
    """Update a room"""
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

@rooms_bp.route('/api/rooms/<int:room_id>', methods=['DELETE'])
@admin_required
def delete_room(room_id):
    """Delete a room and move to deleted_items"""
    room = Room.query.get_or_404(room_id)
    
    # Check if room has products
    if room.products:
        return jsonify({'error': 'Cannot delete room with products. Move products to another room first.'}), 400
    
    # Store room data in deleted_items
    deleted_item = DeletedItem(
        original_id=room.id,
        item_type='room',
        data=room.to_dict(),
        deleted_at=datetime.now(),
        expiry_date=datetime.now() + timedelta(days=30)
    )
    
    db.session.add(deleted_item)
    db.session.delete(room)
    db.session.commit()
    
    return jsonify({'message': 'Room deleted successfully'}), 200

@rooms_bp.route('/api/rooms/<int:room_id>/products', methods=['GET'])
@token_required
def get_room_products(room_id):
    """Get all products in a room"""
    room = Room.query.get_or_404(room_id)
    products = Product.query.filter_by(room_id=room_id).all()
    return jsonify([product.to_dict() for product in products]), 200

@rooms_bp.route('/api/products/<int:product_id>/room', methods=['PUT'])
@admin_required
def update_product_room(product_id):
    """Update a product's room"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    if 'room_id' not in data:
        return jsonify({'error': 'Room ID is required'}), 400
    
    # If room_id is None, it means removing the product from any room
    if data['room_id'] is not None:
        room = Room.query.get(data['room_id'])
        if not room:
            return jsonify({'error': 'Room not found'}), 404
    
    product.room_id = data['room_id']
    db.session.commit()
    
    return jsonify(product.to_dict()), 200


@rooms_bp.route('/api/deleted-items', methods=['GET'])
@token_required
def get_deleted_items():
    """Get all deleted items"""
    deleted_items = DeletedItem.query.all()
    return jsonify([item.to_dict() for item in deleted_items]), 200

@rooms_bp.route('/api/deleted-items/<int:item_id>/restore', methods=['POST'])
@admin_required
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
    elif deleted_item.item_type == 'product':
        # Restore product
        product_data = deleted_item.data
        new_product = Product(
            product_name=product_data['product_name'],
            product_type=product_data['product_type'],
            category=product_data['category'],
            product_code=product_data.get('product_code'),
            manufacturer=product_data.get('manufacturer'),
            qr_code=product_data['qr_code'],
            price_in_kshs=product_data['price_in_kshs'],
            quantity=product_data['quantity'],
            unit_of_measure=product_data['unit_of_measure'],
            concentration=product_data.get('concentration'),
            storage_temperature=product_data.get('storage_temperature'),
            hazard_level=product_data.get('hazard_level'),
            protocol_link=product_data.get('protocol_link'),
            msds_link=product_data.get('msds_link'),
            room_id=product_data.get('room_id')
        )
        db.session.add(new_product)
    
    db.session.delete(deleted_item)
    db.session.commit()
    
    return jsonify({'message': f'{deleted_item.item_type.capitalize()} restored successfully'}), 200

@rooms_bp.route('/api/deleted-items/<int:item_id>', methods=['DELETE'])
@admin_required
def permanently_delete_item(item_id):
    """Permanently delete an item"""
    deleted_item = DeletedItem.query.get_or_404(item_id)
    db.session.delete(deleted_item)
    db.session.commit()
    
    return jsonify({'message': f'{deleted_item.item_type.capitalize()} permanently deleted'}), 200