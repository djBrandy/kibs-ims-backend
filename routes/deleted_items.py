from flask import Blueprint, jsonify, request
from app.database import db
from app.models import DeletedItem, Product, Room, Supplier, User, PendingDelete
import json
from datetime import datetime, timedelta
from flask_cors import cross_origin, CORS

deleted_items_bp = Blueprint(
    'deleted_items', __name__, url_prefix='/api/deleted-items')

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
    """Get all deleted items including pending deletes"""

    # Get items from DeletedItem table
    deleted_items = [item.to_dict() for item in DeletedItem.query.all()]

    # Get items from PendingDelete table
    pending_deletes = PendingDelete.query.filter_by(status='pending').all()

    print(f"Found {len(pending_deletes)} pending delete items")
    for pd in pending_deletes:
        print(
            f"PendingDelete ID: {pd.id}, worker_id: {pd.worker_id}, product_id: {pd.product_id}, room_id: {pd.room_id}, reason: {pd.reason}")

    pending_items = []
    for pd in pending_deletes:
        # Force all entries with no product_id and no room_id to be worker type
        if not pd.product_id and not pd.room_id:
            worker = User.query.get(pd.worker_id)
            if worker:
                worker_data = {
                    'username': worker.username,
                    'email': worker.email,
                    'role': worker.role or 'worker',
                    'is_active': worker.is_active
                }
            else:
                worker_data = {
                    'username': f"Worker {pd.worker_id}",
                    'email': f"worker{pd.worker_id}@example.com",
                    'role': 'worker',
                    'is_active': False
                }

            item_data = {
                'id': f"pending_{pd.id}",
                'original_id': pd.worker_id,
                'item_type': 'worker',
                'data': worker_data,
                'deleted_at': pd.timestamp.isoformat() if pd.timestamp else datetime.now().isoformat(),
                'expiry_date': ((pd.timestamp if pd.timestamp else datetime.now()) + timedelta(days=30)).isoformat(),
                'days_remaining': 30,
                'pending': True,
                'reason': pd.reason
            }
            pending_items.append(item_data)
            continue

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

    # Force all pending deletes with no product_id and no room_id to be worker type
    for item in all_items:
        if item.get('pending') and not item.get('data', {}).get('product_name') and not item.get('data', {}).get('name'):
            item['item_type'] = 'worker'

            # If we don't have proper worker data, create it
            if 'username' not in item.get('data', {}):
                worker_id = item.get('original_id')
                worker = User.query.get(worker_id) if worker_id else None

                if worker:
                    item['data'] = {
                        'username': worker.username,
                        'email': worker.email,
                        'role': worker.role or 'worker',
                        'is_active': worker.is_active
                    }
                else:
                    item['data'] = {
                        'username': f"Worker {worker_id or item.get('id', 'Unknown')}",
                        'email': f"worker{worker_id or 'unknown'}@example.com",
                        'role': 'worker',
                        'is_active': False
                    }

    print(f"Returning {len(all_items)} items")
    for item in all_items:
        print(f"Item: {item.get('id')}, type: {item.get('item_type')}")

    return jsonify(all_items)


@deleted_items_bp.route('/<item_id>/restore', methods=['POST'])
@cross_origin()
def restore_item(item_id):
    """Restore a deleted item"""
    # Check if this is a pending delete item
    if str(item_id).startswith('pending_'):
        from app.models import PendingDelete
        try:
            pending_id = int(item_id.replace('pending_', ''))
            pending_delete = PendingDelete.query.get_or_404(pending_id)

            # Delete the pending delete entry
            db.session.delete(pending_delete)
            db.session.commit()

            # Determine the type of item that was restored
            item_type = "unknown"
            if pending_delete.product_id:
                item_type = "product"
            elif pending_delete.room_id:
                item_type = "room"
            elif pending_delete.worker_id:
                item_type = "worker"

            return jsonify({"message": f"{item_type.capitalize()} deletion cancelled successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to cancel pending deletion: {str(e)}"}), 500

    # Regular deleted item
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
        elif deleted_item.item_type == 'worker':
            from app.models import User
            worker = User(
                id=deleted_item.original_id,
                **{k: v for k, v in deleted_item.data.items() if k != 'id'}
            )
            # Set password hash if not present
            if not worker.password_hash:
                worker.set_password('defaultpassword')
            db.session.add(worker)

        # Remove the item from deleted records and commit
        db.session.delete(deleted_item)
        db.session.commit()

        return jsonify({"message": f"{deleted_item.item_type.capitalize()} restored successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to restore item: {str(e)}"}), 500


@deleted_items_bp.route('/<item_id>', methods=['DELETE'])
@cross_origin()
def permanently_delete_item(item_id):
    """Permanently delete an item"""
    # Check if this is a pending delete item
    if str(item_id).startswith('pending_'):
        from app.models import PendingDelete
        try:
            pending_id = int(item_id.replace('pending_', ''))
            pending_delete = PendingDelete.query.get_or_404(pending_id)

            # Determine the type of item
            item_type = "unknown"
            if pending_delete.product_id:
                item_type = "product"
            elif pending_delete.room_id:
                item_type = "room"
            elif pending_delete.worker_id:
                item_type = "worker"

            # Delete the pending delete entry
            db.session.delete(pending_delete)
            db.session.commit()

            return jsonify({"message": f"Pending {item_type} deletion permanently removed"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to delete pending item: {str(e)}"}), 500

    # Regular deleted item
    try:
        deleted_item = DeletedItem.query.get_or_404(int(item_id))
        db.session.delete(deleted_item)
        db.session.commit()
        return jsonify({"message": f"{deleted_item.item_type.capitalize()} permanently deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete item: {str(e)}"}), 500


# for appending to the deleted items table@deleted_items_bp.route('', methods=['POST'])
@cross_origin()
def add_deleted_item():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['original_id', 'item_type', 'data']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
            
    try:
        new_item = DeletedItem(
            original_id=data.get('original_id'),
            item_type=data.get('item_type'),
            data=data.get('data'),
            deleted_at=datetime.utcnow()
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify(new_item.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
