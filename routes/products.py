from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models import Product

product_bp = Blueprint('products', __name__, url_prefix='/api/products')


@product_bp.route('/', methods=['GET'])
def get_all_products():
    """Get all products with optional filtering"""
    try:

        category = request.args.get('category')
        product_type = request.args.get('product_type')
        low_stock = request.args.get('low_stock', type=bool)
        
        query = Product.query
        
        if category:
            query = query.filter(Product.category == category)
        if product_type:
            query = query.filter(Product.product_type == product_type)
        if low_stock is not None:
            query = query.filter(Product.low_stock_alert == low_stock)
            
        products = query.all()
        
        return jsonify([{
            'id': product.id,
            'product_name': product.product_name,
            'product_code': product.product_code,
            'price_in_kshs': product.price_in_kshs,
            'category': product.category,
            'product_type': product.product_type,
            'manufacturer': product.manufacturer,
            'storage_location': product.storage_location,
            'low_stock_alert': product.low_stock_alert,
            
        } for product in products]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        
        return jsonify({
            'id': product.id,
            'product_name': product.product_name,
            'product_code': product.product_code,
            'price_in_kshs': product.price_in_kshs,
            'product_type': product.product_type,
            'storage_temperature': product.storage_temperature,
            'hazard_level': product.hazard_level,
            'protocol_link': product.protocol_link,
            'msds_link': product.msds_link,
            'low_stock_alert': product.low_stock_alert,
            'checkbox_expiry_date': product.checkbox_expiry_date,
            'checkbox_hazardous_material': product.checkbox_hazardous_material,
            'checkbox_controlled_substance': product.checkbox_controlled_substance,
            'checkbox_requires_regular_calibration': product.checkbox_requires_regular_calibration,
            'special_instructions': product.special_instructions,
            'category': product.category,
            'manufacturer': product.manufacturer,
            'expiration_date': product.expiration_date.isoformat() if product.expiration_date else None,
            'storage_location': product.storage_location,
            'supplier_information': product.supplier_information,
            'date_of_entry': product.date_of_entry.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/', methods=['POST'])
def create_product():
    """Create a new product"""
    try:
        data = request.get_json()
        
        required_fields = ['product_name', 'price_in_kshs', 'product_type', 'category', 
                          'product_code', 'manufacturer', 'storage_location', 'supplier_information']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        expiration_date = None
        if 'expiration_date' in data and data['expiration_date']:
            try:
                expiration_date = datetime.strptime(data['expiration_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid expiration date format. Use YYYY-MM-DD'}), 400
        
        product = Product(
            product_name=data['product_name'],
            price_in_kshs=data['price_in_kshs'],
            product_type=data['product_type'],
            storage_temperature=data.get('storage_temperature'),
            hazard_level=data.get('hazard_level'),
            protocol_link=data.get('protocol_link'),
            msds_link=data.get('msds_link'),
            low_stock_alert=data.get('low_stock_alert', False),
            product_images=data.get('product_images'),
            checkbox_expiry_date=data.get('checkbox_expiry_date', False),
            checkbox_hazardous_material=data.get('checkbox_hazardous_material', False),
            checkbox_controlled_substance=data.get('checkbox_controlled_substance', False),
            checkbox_requires_regular_calibration=data.get('checkbox_requires_regular_calibration', False),
            special_instructions=data.get('special_instructions'),
            category=data['category'],
            product_code=data['product_code'],
            manufacturer=data['manufacturer'],
            expiration_date=expiration_date,
            storage_location=data['storage_location'],
            supplier_information=data['supplier_information']
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({'message': 'Product created successfully', 'id': product.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update an existing product"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        if 'product_name' in data:
            product.product_name = data['product_name']
        if 'price_in_kshs' in data:
            product.price_in_kshs = data['price_in_kshs']
        if 'product_type' in data:
            product.product_type = data['product_type']
        if 'storage_temperature' in data:
            product.storage_temperature = data['storage_temperature']
        if 'hazard_level' in data:
            product.hazard_level = data['hazard_level']
        if 'protocol_link' in data:
            product.protocol_link = data['protocol_link']
        if 'msds_link' in data:
            product.msds_link = data['msds_link']
        if 'low_stock_alert' in data:
            product.low_stock_alert = data['low_stock_alert']
        if 'product_images' in data:
            product.product_images = data['product_images']
        if 'checkbox_expiry_date' in data:
            product.checkbox_expiry_date = data['checkbox_expiry_date']
        if 'checkbox_hazardous_material' in data:
            product.checkbox_hazardous_material = data['checkbox_hazardous_material']
        if 'checkbox_controlled_substance' in data:
            product.checkbox_controlled_substance = data['checkbox_controlled_substance']
        if 'checkbox_requires_regular_calibration' in data:
            product.checkbox_requires_regular_calibration = data['checkbox_requires_regular_calibration']
        if 'special_instructions' in data:
            product.special_instructions = data['special_instructions']
        if 'category' in data:
            product.category = data['category']
        if 'product_code' in data:
            product.product_code = data['product_code']
        if 'manufacturer' in data:
            product.manufacturer = data['manufacturer']
        if 'expiration_date' in data:
            product.expiration_date = datetime.strptime(data['expiration_date'], '%Y-%m-%d').date() if data['expiration_date'] else None
        if 'storage_location' in data:
            product.storage_location = data['storage_location']
        if 'supplier_information' in data:
            product.supplier_information = data['supplier_information']
        
        db.session.commit()
        
        return jsonify({'message': 'Product updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    try:
        product = Product.query.get_or_404(product_id)
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'message': 'Product deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500