from flask import Blueprint, jsonify, request
from app import db
from app.models import DeletedItem, Product, Room, Supplier
import json
from datetime import datetime
from flask_cors import cross_origin, CORS

deleted_items_bp = Blueprint('deleted_items', __name__, url_prefix='/api/deleted-items')

# Apply CORS specifically to this blueprint without the Authorization header
CORS(
    deleted_items_bp,
    origins=["http://localhost:5173", "https://kibs-ims.vercel.app"],
    allow_headers=["Content-Type", "X-API-Key"],
    supports_credentials=True
)

@deleted_items_bp.route('', methods=['GET'])
@cross_origin()
def get_deleted_items():
    """Get all deleted items"""
    deleted_items = DeletedItem.query.all()
    return jsonify([item.to_dict() for item in deleted_items])

@deleted_items_bp.route('/<int:item_id>/restore', methods=['POST'])
@cross_origin()
def restore_item(item_id):
    """Restore a deleted item"""
    deleted_item = DeletedItem.query.get_or_404(item_id)
    
    try:
        # Restore based on item type
        if deleted_item.item_type == 'product':
            product = Product(
                id=deleted_item.original_id,
                **{k: v for k, v in deleted_item.data.items() if k != 'id'}
            )
            db.session.add(product)
        elif deleted_item.item_type == 'room':
            room = Room(
                id=deleted_item.original_id,
                **{k: v for k, v in deleted_item.data.items() if k != 'id'}
            )
            db.session.add(room)
        elif deleted_item.item_type == 'supplier':
            supplier = Supplier(
                id=deleted_item.original_id,
                **{k: v for k, v in deleted_item.data.items() if k != 'id'}
            )
            db.session.add(supplier)
        
        # Remove the item from deleted records and commit
        db.session.delete(deleted_item)
        db.session.commit()
        
        return jsonify({"message": f"{deleted_item.item_type.capitalize()} restored successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to restore item: {str(e)}"}), 500

@deleted_items_bp.route('/<int:item_id>', methods=['DELETE'])
@cross_origin()
def permanently_delete_item(item_id):
    """Permanently delete an item"""
    deleted_item = DeletedItem.query.get_or_404(item_id)
    
    try:
        db.session.delete(deleted_item)
        db.session.commit()
        return jsonify({"message": f"{deleted_item.item_type.capitalize()} permanently deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete item: {str(e)}"}), 500