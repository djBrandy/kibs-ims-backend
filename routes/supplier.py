from flask import Blueprint, request, jsonify
from app import db, Supplier
from datetime import datetime
from flask_cors import cross_origin
from routes.auth import login_required

supplier_bp = Blueprint('supplier', __name__, url_prefix='/api/suppliers')

@supplier_bp.route('/', methods=['GET', 'OPTIONS'])
@cross_origin()
@login_required
def get_all_suppliers():
    if request.method == 'OPTIONS':
        return '', 200
    
    suppliers = Supplier.query.all()
    return jsonify([supplier.to_dict() for supplier in suppliers]), 200

@supplier_bp.route('/<int:supplier_id>', methods=['GET', 'OPTIONS'])
@cross_origin()
@login_required
def get_supplier(supplier_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    supplier = Supplier.query.get_or_404(supplier_id)
    return jsonify(supplier.to_dict()), 200

@supplier_bp.route('/', methods=['POST', 'OPTIONS'])
@cross_origin()
@login_required
def create_supplier():
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.get_json()
    
    if not data.get('shop_name') or not data.get('primary_contact'):
        return jsonify({'error': 'Shop name and primary contact are required'}), 400
    
    new_supplier = Supplier(
        shop_name=data.get('shop_name'),
        primary_contact=data.get('primary_contact'),
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address'),
        notes=data.get('notes')
    )
    
    db.session.add(new_supplier)
    db.session.commit()
    
    return jsonify(new_supplier.to_dict()), 201

@supplier_bp.route('/<int:supplier_id>', methods=['PUT', 'OPTIONS'])
@cross_origin()
@login_required
def update_supplier(supplier_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    supplier = Supplier.query.get_or_404(supplier_id)
    data = request.get_json()
    
    if not data.get('shop_name') or not data.get('primary_contact'):
        return jsonify({'error': 'Shop name and primary contact are required'}), 400
    
    supplier.shop_name = data.get('shop_name')
    supplier.primary_contact = data.get('primary_contact')
    supplier.phone = data.get('phone')
    supplier.email = data.get('email')
    supplier.address = data.get('address')
    supplier.notes = data.get('notes')
    supplier.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(supplier.to_dict()), 200

@supplier_bp.route('/<int:supplier_id>', methods=['DELETE', 'OPTIONS'])
@cross_origin()
@login_required
def delete_supplier(supplier_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    supplier = Supplier.query.get_or_404(supplier_id)
    
    db.session.delete(supplier)
    db.session.commit()
    
    return jsonify({'message': 'Supplier deleted successfully'}), 200