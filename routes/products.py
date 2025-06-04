from flask import Blueprint, request, jsonify, g # type: ignore
from datetime import datetime
from app import db
from app import Product
import base64
import random
from routes.auth import login_required
import traceback
from app.models import Product, PendingDelete, AlertNotification, Worker, Admin, AuditLog, db
from flask_jwt_extended import jwt_required, get_jwt_identity # type: ignore

product_bp = Blueprint('products', __name__, url_prefix='/api/products')


@product_bp.route('/', methods=['GET'])
@login_required
def get_all_products():
    try:
        # from flask import g
        
        category = request.args.get('category')
        product_type = request.args.get('product_type')
        low_stock = request.args.get('low_stock', type=bool)
        detailed = request.args.get('detailed', type=bool, default=False)

        query = Product.query
        
        # If user is a worker, hide products marked as hidden from workers
        try:
            if hasattr(g, 'user') and g.user and g.user.role == 'worker':
                # Check if hidden_from_workers column exists
                if hasattr(Product, 'hidden_from_workers'):
                    query = query.filter(Product.hidden_from_workers == False)
        except Exception:
            # If column doesn't exist yet, continue without filtering
            pass

        if category:
            query = query.filter(Product.category == category)
        if product_type:
            query = query.filter(Product.product_type == product_type)
        if low_stock is not None:
            if low_stock:  
                query = query.filter(Product.quantity <= Product.low_stock_alert)
            else:  
                query = query.filter(Product.quantity > Product.low_stock_alert)

        products = query.all()

        from flask import g
        
        # Check if user is admin to include QR code
        is_admin = hasattr(g, 'user') and g.user and g.user.role == 'admin'
        
        if detailed:
            result = []
            for product in products:
                product_dict = product.to_dict(include_qr=is_admin)
                if product.product_images:
                    product_dict["product_images"] = base64.b64encode(product.product_images).decode('utf-8')
                result.append(product_dict)
            return jsonify(result), 200
        else:
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
                    "manufacturer": product.manufacturer,
                    "low_stock_alert": product.low_stock_alert,
                    "expiration_date": product.expiration_date.isoformat() if product.expiration_date else None,
                }
                # Only include QR code for admin users
                if is_admin:
                    product_dict["qr_code"] = product.qr_code
                result.append(product_dict)
            return jsonify(result), 200

    except Exception as e:
        # print(f"Error fetching products: {str(e)}")
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
            "product_images": base64.b64encode(product.product_images).decode('utf-8') if product.product_images else None,
            "date_of_entry": product.date_of_entry.isoformat() if product.date_of_entry else None
        }), 200

    except Exception as e:
        # print(f"Error getting product {product_id}: {str(e)}")
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
            'quantity', 'unit_of_measure', 'room_id'
        ]

        for field in required_fields:
            if field == 'room_id':
                if not data.get(field) and data.get(field) != 0:
                    return jsonify({'error': f'{field} is required'}), 400
            elif not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        expiration_date = None
        if data.get('expiration_date'):
            try:
                expiration_date = datetime.strptime(data['expiration_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid expiration date format. Use YYYY-MM-DD'}), 400

        image_data = image_file.read() if image_file else None

        try:
            price_str = data['price_in_kshs']
            if isinstance(price_str, str):
                price_str = price_str.replace(',', '')
            price = float(price_str)
        except (ValueError, TypeError):
             return jsonify({'error': 'Invalid price value. Must be a number.'}), 400

        try:
            quantity = int(data['quantity'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid quantity value. Must be an integer.'}), 400

        try:
            low_stock_alert_value = data.get('low_stock_alert', '10')
            if isinstance(low_stock_alert_value, str) and low_stock_alert_value.strip() == '':
                low_stock_alert = 10
            else:
                low_stock_alert = int(low_stock_alert_value)
        except (ValueError, TypeError):
             return jsonify({'error': 'Invalid low stock alert value. Must be an integer.'}), 400

        try:
            concentration_value = None
            if data.get('concentration'):
                conc_input = data['concentration']
                if isinstance(conc_input, str) and conc_input.strip():
                    concentration_value = float(conc_input)
                elif not isinstance(conc_input, str) and conc_input is not None:
                    concentration_value = float(conc_input)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid concentration value. Must be a number.'}), 400

        try:
            product = Product(
                product_name=data['product_name'],
                price_in_kshs=price,
                product_type=data['product_type'],
                category=data['category'],
                product_code=data['product_code'],
                manufacturer=data.get('manufacturer'),
                qr_code=data.get('qr_code'),
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
                product_images=image_data,
                room_id=data.get('room_id')
            )
        except Exception as e:
             db.session.rollback()
             error_details = traceback.format_exc()
            #  print(f"Error during product object creation: {str(e)}")
            #  print(f"Traceback: {error_details}")
             return jsonify({'error': f'Server error during product creation: {str(e)}'}), 500

        db.session.add(product)
        db.session.commit()

        return jsonify({'message': 'Product created successfully', 'id': product.id}), 201

    except Exception as e:
        db.session.rollback()
        error_details = traceback.format_exc()
        # print(f"Error creating product: {str(e)}")
        # print(f"Traceback: {error_details}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500
    


@product_bp.route('/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
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
        # print(f"Error updating product {product_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@product_bp.route('/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    try:
        from flask import g
        from sqlalchemy import text
        from app.models import InventoryAnalytics
        
        # Check if user is admin or worker
        is_admin = hasattr(g, 'user') and g.user and g.user.role == 'admin'
        
        if is_admin:
            # Admin can actually delete the product
            try:
                # Get the product first to check if it exists
                product = Product.query.get(product_id)
                if not product:
                    return jsonify({'message': 'Product not found'}), 404
                
                # Use SQLAlchemy ORM to delete related records safely
                AuditLog.query.filter_by(product_id=product_id).delete()
                
                # Use try/except for each table in case it doesn't exist
                try:
                    InventoryAnalytics.query.filter_by(product_id=product_id).delete()
                except:
                    pass
                    
                try:
                    AlertNotification.query.filter_by(product_id=product_id).delete()
                except:
                    pass
                    
                try:
                    Purchase.query.filter_by(product_id=product_id).delete()
                except:
                    pass
                
                # Try to delete order items if they exist
                try:
                    db.session.execute(text(f"DELETE FROM order_items WHERE product_id = {product_id}"))
                except:
                    pass  # Ignore if table doesn't exist
                
                # Finally delete the product
                db.session.delete(product)
                db.session.commit()
                
                return jsonify({'message': 'Product deleted successfully'}), 200
            except Exception as inner_e:
                db.session.rollback()
                # Try a simpler approach if the first one fails
                try:
                    db.session.execute(text(f"DELETE FROM products WHERE id = {product_id}"))
                    db.session.commit()
                    return jsonify({'message': 'Product deleted successfully'}), 200
                except:
                    raise inner_e
        else:
            # Workers cannot delete products, only request deletion
            return jsonify({'error': 'Only administrators can delete products. Please contact an admin if you need a product removed.'}), 403
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@product_bp.route('/pending-delete-requests', methods=['GET'])
@login_required
def get_pending_delete_requests():
    try:
        from flask import g
        
        # Only admins can see pending delete requests
        is_admin = hasattr(g, 'user') and g.user and g.user.role == 'admin'
        if not is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Get all pending delete requests with product and worker info
        pending_requests = PendingDelete.query.filter_by(status='pending').all()
        
        result = []
        for request in pending_requests:
            product = Product.query.get(request.product_id)
            worker = User.query.get(request.worker_id)
            
            if product and worker:
                result.append({
                    'id': request.id,
                    'product_id': request.product_id,
                    'product_name': product.product_name,
                    'worker_id': request.worker_id,
                    'worker_name': worker.username,
                    'timestamp': request.timestamp.isoformat(),
                    'status': request.status
                })
                
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@product_bp.route('/delete-request/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_delete_request(request_id):
    try:
        from flask import g
        
        # Only admins can approve delete requests
        is_admin = hasattr(g, 'user') and g.user and g.user.role == 'admin'
        if not is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Get the delete request
        delete_request = PendingDelete.query.get_or_404(request_id)
        product = Product.query.get(delete_request.product_id)
        worker = User.query.get(delete_request.worker_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
            
        # Update request status
        delete_request.status = 'approved'
        
        # Actually delete the product
        db.session.execute(f"DELETE FROM audit_logs WHERE product_id = {product.id}")
        db.session.execute(f"DELETE FROM inventory_analytics WHERE product_id = {product.id}")
        db.session.execute(f"DELETE FROM alert_notifications WHERE product_id = {product.id}")
        db.session.execute(f"DELETE FROM purchases WHERE product_id = {product.id}")
        db.session.execute(f"DELETE FROM order_items WHERE product_id = {product.id}")
        
        # Add audit log before deleting product
        audit = AuditLog(
            product_id=1,  # Use placeholder since product will be deleted
            user_id=g.user.id,
            action_type='delete_approved',
            notes=f"Admin approved deletion of product {product.product_name} requested by {worker.username if worker else 'unknown'}"
        )
        db.session.add(audit)
        
        # Now delete the product
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'message': 'Delete request approved and product deleted'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/delete-request/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_delete_request(request_id):
    try:
        from flask import g
        
        # Only admins can reject delete requests
        is_admin = hasattr(g, 'user') and g.user and g.user.role == 'admin'
        if not is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Get the delete request
        delete_request = PendingDelete.query.get_or_404(request_id)
        product = Product.query.get(delete_request.product_id)
        worker = User.query.get(delete_request.worker_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
            
        # Update request status
        delete_request.status = 'rejected'
        
        # Make product visible to workers again
        product.hidden_from_workers = False
        
        # Add audit log
        audit = AuditLog(
            product_id=product.id,
            user_id=g.user.id,
            action_type='delete_rejected',
            notes=f"Admin rejected deletion of product {product.product_name} requested by {worker.username if worker else 'unknown'}"
        )
        db.session.add(audit)
        
        db.session.commit()
        
        return jsonify({'message': 'Delete request rejected and product made visible again'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500