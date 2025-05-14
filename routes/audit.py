# ims-kibs-backend/routes/audit.py
from flask import Blueprint, request, jsonify
from app import db, Product
from datetime import datetime

audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit')
@audit_bp.route('/scan/<barcode>', methods=['GET'])
def scan_product(barcode):
    """Check if product exists by barcode/QR code"""
    try:
        # Add debug logging
        print(f"Searching for product with QR code: {barcode}")
        
        # Try to find the product with exact match
        product = Product.query.filter_by(qr_code=barcode).first()
        
        # If not found, try with string conversion
        if not product:
            print("Product not found with direct match, trying string conversion")
            product = Product.query.filter(Product.qr_code == str(barcode)).first()
        
        if not product:
            print("Product not found after string conversion")
            # Debug: List all QR codes in the database
            all_qr_codes = [p.qr_code for p in Product.query.all()]
            print(f"Available QR codes in database: {all_qr_codes}")
            return jsonify({'error': 'Product not found'}), 404
            
        print(f"Product found: {product.product_name}")
        return jsonify({
            'id': product.id,
            'product_name': product.product_name,
            'product_code': product.product_code,
            'quantity': product.quantity,
            'unit_of_measure': product.unit_of_measure,
            'concentration': product.concentration,
            'special_instructions': product.special_instructions
        }), 200
        
    except Exception as e:
        print(f"Error in scan_product: {str(e)}")
        return jsonify({'error': str(e)}), 500

@audit_bp.route('/update/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update product quantity, concentration and notes"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        if 'quantity' in data:
            product.quantity = int(data['quantity'])
            
        if 'concentration' in data:
            product.concentration = float(data['concentration']) if data['concentration'] else None
            
        if 'special_instructions' in data:
            product.special_instructions = data['special_instructions']
        
        # Add audit log entry
        # This would be implemented with a proper audit log table
        
        db.session.commit()
        
        return jsonify({
            'message': 'Product updated successfully',
            'product': {
                'id': product.id,
                'product_name': product.product_name,
                'quantity': product.quantity,
                'concentration': product.concentration,
                'special_instructions': product.special_instructions
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
