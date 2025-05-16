from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app import Product
import random
from routes.auth import login_required
import traceback

product_bp = Blueprint('products', __name__, url_prefix='/api/products')


@product_bp.route('/', methods=['GET'])
@login_required
def get_all_products():
    try:
        category = request.args.get('category')
        product_type = request.args.get('product_type')
        low_stock = request.args.get('low_stock', type=bool)
        detailed = request.args.get('detailed', type=bool, default=False)

        query = Product.query

        if category:
            query = query.filter(Product.category == category)
        if product_type:
            query = query.filter(Product.product_type == product_type)
        if low_stock is not None:
            if low_stock:  # True means return only low-stock products
                query = query.filter(Product.quantity <= Product.low_stock_alert)
            else:  # False means return products above low stock threshold
                query = query.filter(Product.quantity > Product.low_stock_alert)

        products = query.all()

        if detailed:
            # Return full product details
            return jsonify([{
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
                "product_images": product.product_images.decode('utf-8') if product.product_images else None,
                "date_of_entry": product.date_of_entry.isoformat() if product.date_of_entry else None
            } for product in products]), 200
        else:
            # Return basic product info
            return jsonify([{
                "id": product.id,
                "product_name": product.product_name,
                "product_code": product.product_code,
                "qr_code": product.qr_code,
                "price_in_kshs": product.price_in_kshs,
                "quantity": product.quantity,
                "unit_of_measure": product.unit_of_measure,
                "category": product.category,
                "product_type": product.product_type,
                "manufacturer": product.manufacturer,
                "low_stock_alert": product.low_stock_alert,
                "expiration_date": product.expiration_date.isoformat() if product.expiration_date else None,
            } for product in products]), 200

    except Exception as e:
        print(f"Error fetching products: {str(e)}")
        return jsonify({'error': str(e)}), 500


@product_bp.route('/<int:product_id>', methods=['GET'])
@login_required
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
            "product_images": product.product_images.decode('utf-8') if product.product_images else None,
            "date_of_entry": product.date_of_entry.isoformat() if product.date_of_entry else None
        }), 200

    except Exception as e:
        print(f"Error getting product {product_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500
    

def to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == 'true'
    return False



@product_bp.route('/', methods=['POST'])
@login_required
def create_product():
    try:
        if request.content_type == 'application/json':
            data = request.get_json() 
        else:
            data = request.form  

        image_file = request.files.get('product_images') 
        if image_file and not image_file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return jsonify({'error': 'Invalid image format. Only PNG, JPG, JPEG, and GIF are allowed.'}), 400
        
        required_fields = [
            'product_name', 'price_in_kshs', 'product_type',
            'category', 'product_code', 'manufacturer',
            'quantity', 'unit_of_measure'
        ]

        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        expiration_date = None
        if data.get('expiration_date'):
            try:
                expiration_date = datetime.strptime(data['expiration_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid expiration date format. Use YYYY-MM-DD'}), 400

        image_data = image_file.read() if image_file else None

        try:
            # Clean and convert numeric values
            price_str = data['price_in_kshs']
            if isinstance(price_str, str):
                price_str = price_str.replace(',', '')
            price = float(price_str)
            
            quantity = int(data['quantity'])
            
            low_stock_alert_value = data.get('low_stock_alert', '10')
            if isinstance(low_stock_alert_value, str) and low_stock_alert_value.strip() == '':
                low_stock_alert = 10
            else:
                low_stock_alert = int(low_stock_alert_value)
            
            concentration_value = None
            if data.get('concentration'):
                if isinstance(data['concentration'], str) and data['concentration'].strip():
                    concentration_value = float(data['concentration'])
                elif not isinstance(data['concentration'], str):
                    concentration_value = float(data['concentration'])
            
            product = Product(
                product_name=data['product_name'],
                price_in_kshs=price,
                product_type=data['product_type'],
                category=data['category'],
                product_code=data['product_code'],
                manufacturer=data['manufacturer'],
                qr_code=data['qr_code'],
                quantity=quantity,
                unit_of_measure=data['unit_of_measure'],
                concentration=concentration_value,
                storage_temperature=data.get('storage_temperature'),
                expiration_date=expiration_date,
                hazard_level=data.get('hazard_level'),
                protocol_link=data.get('protocol_link'),
                msds_link=data.get('msds_link'),
                low_stock_alert=low_stock_alert,
                checkbox_expiry_date=to_bool(data.get('checkbox_expiry_date', 'false')),
                checkbox_hazardous_material=to_bool(data.get('checkbox_hazardous_material', 'false')),
                checkbox_controlled_substance=to_bool(data.get('checkbox_controlled_substance', 'false')),
                checkbox_requires_regular_calibration=to_bool(data.get('checkbox_requires_regular_calibration', 'false')),
                special_instructions=data.get('special_instructions'),
                product_images=image_data
            )
        except ValueError as ve:
            return jsonify({'error': f'Invalid value format: {str(ve)}'}), 400

        db.session.add(product)
        db.session.commit()

        return jsonify({'message': 'Product created successfully', 'id': product.id}), 201

    except Exception as e:
        db.session.rollback()
        error_details = traceback.format_exc()
        print(f"Error creating product: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500
    


@product_bp.route('/<int:product_id>', methods=['PUT'])
@login_required
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
        print(f"Error updating product {product_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@product_bp.route('/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    """Delete a product"""
    try:
        print(f"Attempting to delete product with ID: {product_id}")
        
        # First, delete related audit logs
        db.session.execute(f"DELETE FROM audit_logs WHERE product_id = {product_id}")
        
        # Delete related inventory analytics
        db.session.execute(f"DELETE FROM inventory_analytics WHERE product_id = {product_id}")
        
        # Delete related alert notifications
        db.session.execute(f"DELETE FROM alert_notifications WHERE product_id = {product_id}")
        
        # Delete any related purchases
        db.session.execute(f"DELETE FROM purchases WHERE product_id = {product_id}")
        
        # Delete any related order items
        db.session.execute(f"DELETE FROM order_items WHERE product_id = {product_id}")
        
        # Finally delete the product
        db.session.execute(f"DELETE FROM products WHERE id = {product_id}")
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({'message': 'Product deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting product: {str(e)}")
        return jsonify({'error': str(e)}), 500