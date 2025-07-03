from flask import Blueprint, request, jsonify, send_file
import qrcode
import base64
import os
import json
from io import BytesIO
from app.database import db
from app.models import Product

qr_code_bp = Blueprint('qr_codes', __name__, url_prefix='/api/qr-codes')

QR_CODES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qr_codes.json')
QR_QUEUE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qr_queue.json')

def load_qr_codes():
    if os.path.exists(QR_CODES_FILE):
        with open(QR_CODES_FILE, 'r') as file:
            return json.load(file)
    return []

def save_qr_codes(qr_codes):
    with open(QR_CODES_FILE, 'w') as file:
        json.dump(qr_codes, file)

def load_qr_queue():
    if os.path.exists(QR_QUEUE_FILE):
        with open(QR_QUEUE_FILE, 'r') as file:
            return json.load(file)
    return []

def save_qr_queue(queue):
    with open(QR_QUEUE_FILE, 'w') as file:
        json.dump(queue, file)

@qr_code_bp.route('/add', methods=['POST'])
def add_qr_code():
    """Add a new QR code to the collection"""
    try:
        data = request.json
        qr_code = data.get('qr_code')
        if not qr_code:
            return jsonify({'error': 'QR code is required'}), 400

        qr_codes = load_qr_codes()
        qr_codes.append(qr_code)
        save_qr_codes(qr_codes)

        return jsonify({'message': 'QR code added successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@qr_code_bp.route('/remove', methods=['POST'])
def remove_qr_code():
    """Remove a QR code from the collection"""
    try:
        data = request.json
        qr_code = data.get('qr_code')
        qr_codes = load_qr_codes()
        qr_codes = [code for code in qr_codes if code != qr_code]
        save_qr_codes(qr_codes)
        return jsonify({'message': 'QR code removed successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@qr_code_bp.route('/remove-all', methods=['POST'])
def remove_all_qr_codes():
    """Remove all QR codes from the collection"""
    try:
        save_qr_codes([])
        return jsonify({'message': 'All QR codes removed successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@qr_code_bp.route('/list', methods=['GET'])
def list_qr_codes():
    """List all QR codes in the system"""
    try:
        qr_codes = load_qr_codes()
        return jsonify(qr_codes), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@qr_code_bp.route('/generate/<qr_code>', methods=['GET'])
def generate_qr_code(qr_code):
    """Generate a QR code as an image (PNG)"""
    try:
        img = qrcode.make(qr_code)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return send_file(buffer, mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# QR Queue Management Routes
@qr_code_bp.route('/add-to-queue', methods=['POST'])
def add_to_queue():
    """Add a product to QR code print queue"""
    try:
        data = request.json
        product_id = data.get('product_id')
        product_name = data.get('product_name')
        product_code = data.get('product_code')
        qr_code = data.get('qr_code', product_code)
        
        if not all([product_id, product_name, product_code]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Generate QR code image
        img = qrcode.make(qr_code)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        queue = load_qr_queue()
        
        # Check if product already in queue
        if any(item['product_id'] == product_id for item in queue):
            return jsonify({'error': 'Product already in queue'}), 400
        
        queue_item = {
            'id': len(queue) + 1,
            'product_id': product_id,
            'product_name': product_name,
            'product_code': product_code,
            'qr_code': qr_code,
            'qr_image': qr_image_base64
        }
        
        queue.append(queue_item)
        save_qr_queue(queue)
        
        return jsonify({'message': 'Product added to QR queue successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@qr_code_bp.route('/get-queue', methods=['GET'])
def get_queue():
    """Get all items in QR code print queue"""
    try:
        queue = load_qr_queue()
        return jsonify(queue), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@qr_code_bp.route('/remove-from-queue/<int:item_id>', methods=['DELETE'])
def remove_from_queue(item_id):
    """Remove an item from QR code print queue"""
    try:
        queue = load_qr_queue()
        queue = [item for item in queue if item['id'] != item_id]
        save_qr_queue(queue)
        return jsonify({'message': 'Item removed from queue successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@qr_code_bp.route('/clear-queue', methods=['DELETE'])
def clear_queue():
    """Clear all items from QR code print queue"""
    try:
        save_qr_queue([])
        return jsonify({'message': 'Queue cleared successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500