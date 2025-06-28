from flask import Blueprint, request, jsonify # type: ignore
from datetime import datetime
from app.database import db
from app.models import Product
import base64
import requests

product_bp = Blueprint('products', __name__, url_prefix='/api/products')

@product_bp.route('/', methods=['GET'])
def get_all_products():
    try:
        category = request.args.get('category')
        product_type = request.args.get('product_type')
        low_stock = request.args.get('low_stock', type=bool)
        room_id = request.args.get('room_id', type=int)
        
        query = Product.query
        
        if category:
            query = query.filter(Product.category == category)
        if product_type:
            query = query.filter(Product.product_type == product_type)
        if low_stock is not None:
            query = query.filter(Product.quantity <= Product.low_stock_alert) if low_stock else query.filter(Product.quantity > Product.low_stock_alert)
        if room_id is not None:
            query = query.filter(Product.room_id == room_id)

        products = query.all()
        
        result = []
        for product in products:
            product_dict = {
                "id": product.id,
                "product_name": product.product_name,
                "product_code": product.product_code,
                "price_in_kshs": product.price_in_kshs,
                "quantity": product.quantity,
                "unit_of_measure": product.unit_of_measure,
                "category": product.category,
                "product_type": product.product_type,
                "qr_code": product.qr_code,
                "room_id": product.room_id,
                "product_images": base64.b64encode(product.product_images).decode('utf-8') if product.product_images else None,
                "date_of_entry": product.date_of_entry.isoformat() if product.date_of_entry else None
            }
            result.append(product_dict)
            
        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


@product_bp.route('/my-outbound-ip')
def get_outbound_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status() # Raise an exception for bad status codes
        ip_data = response.json()
        return {"outbound_ip": ip_data.get('ip', 'Could not determine IP')}
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to get outbound IP: {e}"}, 500




@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)

        return jsonify({
            "id": product.id,
            "product_name": product.product_name,
            "product_type": product.product_type,
            "category": product.category,
            "product_code": product.product_code,
            "manufacturer": product.manufacturer,
            "qr_code": product.qr_code,
            "price_in_kshs": product.price_in_kshs,
            "quantity": product.quantity,
            "unit_of_measure": product.unit_of_measure,
            "concentration": product.concentration,
            "storage_temperature": product.storage_temperature,
            "expiration_date": product.expiration_date.isoformat() if product.expiration_date else None,
            "hazard_level": product.hazard_level,
            "protocol_link": product.protocol_link,
            "msds_link": product.msds_link,
            "low_stock_alert": product.low_stock_alert,
            "checkbox_expiry_date": product.checkbox_expiry_date,
            "checkbox_hazardous_material": product.checkbox_hazardous_material,
            "checkbox_controlled_substance": product.checkbox_controlled_substance,
            "checkbox_requires_regular_calibration": product.checkbox_requires_regular_calibration,
            "special_instructions": product.special_instructions,
            "room_id": product.room_id,
            "product_images": base64.b64encode(product.product_images).decode('utf-8') if product.product_images else None,
            "date_of_entry": product.date_of_entry.isoformat() if product.date_of_entry else None
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/', methods=['POST'])
def create_product():
    try:
        data = request.get_json()
        
        required_fields = ['product_name', 'price_in_kshs', 'product_type', 'category']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        # Helper function to convert string boolean values to Python booleans
        def parse_bool(value):
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() == 'true'
            return bool(value)
            
        product = Product(
            product_name=data['product_name'],
            price_in_kshs=float(data['price_in_kshs']),
            product_type=data['product_type'],
            category=data['category'],
            product_code=data.get('product_code'),
            manufacturer=data.get('manufacturer'),
            qr_code=data.get('qr_code'),
            quantity=int(data.get('quantity', 0)),
            unit_of_measure=data.get('unit_of_measure', 'units'),
            concentration=data.get('concentration'),
            storage_temperature=data.get('storage_temperature'),
            expiration_date=data.get('expiration_date'),
            hazard_level=data.get('hazard_level'),
            protocol_link=data.get('protocol_link'),
            msds_link=data.get('msds_link'),
            low_stock_alert=int(data.get('low_stock_alert', 10)),
            checkbox_expiry_date=parse_bool(data.get('checkbox_expiry_date', False)),
            checkbox_hazardous_material=parse_bool(data.get('checkbox_hazardous_material', False)),
            checkbox_controlled_substance=parse_bool(data.get('checkbox_controlled_substance', False)),
            checkbox_requires_regular_calibration=parse_bool(data.get('checkbox_requires_regular_calibration', False)),
            special_instructions=data.get('special_instructions'),
            room_id=data.get('room_id'),
            product_images=base64.b64decode(data['product_images']) if data.get('product_images') else None
        )

        db.session.add(product)
        db.session.commit()

        return jsonify({'message': 'Product created successfully', 'id': product.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        # Update all fields that are present in the request
        if 'product_name' in data:
            product.product_name = data['product_name']
        if 'product_type' in data:
            product.product_type = data['product_type']
        if 'category' in data:
            product.category = data['category']
        if 'product_code' in data:
            product.product_code = data['product_code']
        if 'manufacturer' in data:
            product.manufacturer = data['manufacturer']
        if 'price_in_kshs' in data:
            product.price_in_kshs = float(data['price_in_kshs'])
        if 'quantity' in data:
            product.quantity = int(data['quantity'])
        if 'unit_of_measure' in data:
            product.unit_of_measure = data['unit_of_measure']
        if 'concentration' in data:
            product.concentration = data['concentration']
        if 'storage_temperature' in data:
            product.storage_temperature = data['storage_temperature']
        if 'expiration_date' in data:
            product.expiration_date = data['expiration_date']
        if 'hazard_level' in data:
            product.hazard_level = data['hazard_level']
        if 'protocol_link' in data:
            product.protocol_link = data['protocol_link']
        if 'msds_link' in data:
            product.msds_link = data['msds_link']
        if 'low_stock_alert' in data:
            product.low_stock_alert = int(data['low_stock_alert'])
        # Helper function to convert string boolean values to Python booleans
        def parse_bool(value):
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() == 'true'
            return bool(value)
            
        if 'checkbox_expiry_date' in data:
            product.checkbox_expiry_date = parse_bool(data['checkbox_expiry_date'])
        if 'checkbox_hazardous_material' in data:
            product.checkbox_hazardous_material = parse_bool(data['checkbox_hazardous_material'])
        if 'checkbox_controlled_substance' in data:
            product.checkbox_controlled_substance = parse_bool(data['checkbox_controlled_substance'])
        if 'checkbox_requires_regular_calibration' in data:
            product.checkbox_requires_regular_calibration = parse_bool(data['checkbox_requires_regular_calibration'])
        if 'special_instructions' in data:
            product.special_instructions = data['special_instructions']
        if 'room_id' in data:
            product.room_id = data['room_id']
        if 'product_images' in data and data['product_images']:
            product.product_images = base64.b64decode(data['product_images'])
        elif 'product_images' in data and data['product_images'] is None:
            product.product_images = None
        
        db.session.commit()
        return jsonify({'message': 'Product updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500