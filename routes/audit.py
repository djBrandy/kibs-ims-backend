# ims-kibs-backend/routes/audit.py
from flask import Blueprint, request, jsonify
from flask import session
from app import db, Product, AuditLog
from datetime import datetime, timedelta
from routes.auth import login_required
import traceback

audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit')

@audit_bp.route('/scan/<barcode>', methods=['GET'])
@login_required
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
            
        # If still not found, try with numeric conversion (in case barcode is stored as a number)
        if not product:
            print("Product not found with string conversion, trying numeric conversion")
            try:
                numeric_barcode = int(barcode)
                product = Product.query.filter(Product.qr_code == str(numeric_barcode)).first()
            except (ValueError, TypeError):
                pass
        
        if not product:
            print("Product not found after all conversion attempts")
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
        error_details = traceback.format_exc()
        print(f"Error in scan_product: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500

@audit_bp.route('/update/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    """Update product quantity, concentration and notes"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        print(f"Updating product {product_id}: {data}")
        
        # Store previous values for logging
        previous_quantity = product.quantity
        previous_concentration = product.concentration
        previous_instructions = product.special_instructions
        
        # Update product fields and create audit logs
        if 'quantity' in data:
            try:
                new_quantity = int(data['quantity'])
                if new_quantity != previous_quantity:
                    # Create audit log for quantity change
                    audit_log = AuditLog(
                        product_id=product.id,
                        user_id=session.get('user_id'),  # Assuming user_id is stored in session
                        action_type='quantity_update',
                        previous_value=str(previous_quantity),
                        new_value=str(new_quantity),
                        notes=data.get('notes', 'Quantity updated')
                    )
                    db.session.add(audit_log)
                    
                    # Update product quantity
                    product.quantity = new_quantity
                    print(f"Updated quantity from {previous_quantity} to {new_quantity}")
            except (ValueError, TypeError) as e:
                return jsonify({'error': f'Invalid quantity value: {str(e)}'}), 400
            
        if 'concentration' in data:
            try:
                if data['concentration'] and str(data['concentration']).strip():
                    new_concentration = float(data['concentration'])
                    if new_concentration != previous_concentration:
                        # Create audit log for concentration change
                        audit_log = AuditLog(
                            product_id=product.id,
                            user_id=session.get('user_id'),
                            action_type='concentration_update',
                            previous_value=str(previous_concentration) if previous_concentration is not None else 'None',
                            new_value=str(new_concentration),
                            notes=data.get('notes', 'Concentration updated')
                        )
                        db.session.add(audit_log)
                        
                        # Update product concentration
                        product.concentration = new_concentration
                        print(f"Updated concentration from {previous_concentration} to {new_concentration}")
                else:
                    if previous_concentration is not None:
                        # Create audit log for clearing concentration
                        audit_log = AuditLog(
                            product_id=product.id,
                            user_id=session.get('user_id'),
                            action_type='concentration_update',
                            previous_value=str(previous_concentration) if previous_concentration is not None else 'None',
                            new_value='None',
                            notes=data.get('notes', 'Concentration cleared')
                        )
                        db.session.add(audit_log)
                        
                        # Clear product concentration
                        product.concentration = None
                        print(f"Cleared concentration (was {previous_concentration})")
            except (ValueError, TypeError) as e:
                return jsonify({'error': f'Invalid concentration value: {str(e)}'}), 400
            
        if 'special_instructions' in data and data['special_instructions'] != product.special_instructions:
            # Create audit log for special instructions change
            audit_log = AuditLog(
                product_id=product.id,
                user_id=session.get('user_id'),
                action_type='notes_update',
                previous_value=previous_instructions if previous_instructions else 'None',
                new_value=data['special_instructions'] if data['special_instructions'] else 'None',
                notes=data.get('notes', 'Special instructions updated')
            )
            db.session.add(audit_log)
            
            # Update product special instructions
            product.special_instructions = data['special_instructions']
            print(f"Updated special instructions from '{previous_instructions}' to '{data['special_instructions']}'")
        
        # Save all changes
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
        error_details = traceback.format_exc()
        print(f"Error updating product {product_id}: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500

@audit_bp.route('/logs', methods=['GET'])
@login_required
def get_audit_logs():
    """Get audit logs with optional filtering"""
    try:
        # Get query parameters
        product_id = request.args.get('product_id', type=int)
        action_type = request.args.get('action_type')
        days = request.args.get('days', type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Start with a base query
        query = AuditLog.query
        
        # Apply filters
        if product_id:
            query = query.filter(AuditLog.product_id == product_id)
        
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)
        
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = query.filter(AuditLog.timestamp >= cutoff_date)
        
        # Order by timestamp descending (newest first)
        query = query.order_by(AuditLog.timestamp.desc())
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute query and convert to list of dictionaries
        logs = [log.to_dict() for log in query.all()]
        
        return jsonify(logs), 200
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error getting audit logs: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500
        
@audit_bp.route('/logs/pdf', methods=['GET'])
@login_required
def get_audit_logs_pdf():
    """Generate PDF of audit logs"""
    try:
        from flask import send_file
        import tempfile
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        
        # Get query parameters
        product_id = request.args.get('product_id', type=int)
        action_type = request.args.get('action_type')
        days = request.args.get('days', type=int)
        
        # Start with a base query
        query = AuditLog.query.join(Product, AuditLog.product_id == Product.id)
        
        # Apply filters
        if product_id:
            query = query.filter(AuditLog.product_id == product_id)
        
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)
        
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = query.filter(AuditLog.timestamp >= cutoff_date)
        
        # Order by timestamp descending (newest first)
        query = query.order_by(AuditLog.timestamp.desc())
        
        # Execute query
        logs = query.all()
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Add title
        title = Paragraph("Audit Logs Report", styles['Heading1'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Add date
        date_text = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        elements.append(date_text)
        elements.append(Spacer(1, 20))
        
        # Create table data
        data = [['Product', 'Action', 'Previous Value', 'New Value', 'Date', 'Time', 'Notes']]
        
        for log in logs:
            timestamp = log.timestamp
            date_str = timestamp.strftime('%Y-%m-%d')
            time_str = timestamp.strftime('%H:%M:%S')
            
            action_type = log.action_type.replace('_', ' ').title()
            
            data.append([
                log.product.product_name,
                action_type,
                log.previous_value or 'N/A',
                log.new_value or 'N/A',
                date_str,
                time_str,
                log.notes or 'N/A'
            ])
        
        # Create table
        table = Table(data)
        
        # Style the table
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('WORDWRAP', (0, 1), (-1, -1), True),
        ])
        table.setStyle(table_style)
        
        # Add table to elements
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        
        # Return the PDF file
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error generating PDF: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500
        
@audit_bp.route('/logs/product/<int:product_id>', methods=['GET'])
@login_required
def get_product_audit_logs(product_id):
    """Get audit logs for a specific product"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        
        # Check if product exists
        product = Product.query.get_or_404(product_id)
        
        # Query audit logs for this product
        logs = AuditLog.query.filter_by(product_id=product_id) \
                            .order_by(AuditLog.timestamp.desc()) \
                            .limit(limit) \
                            .all()
        
        # Convert to list of dictionaries
        logs_data = [log.to_dict() for log in logs]
        
        return jsonify({
            'product': {
                'id': product.id,
                'product_name': product.product_name
            },
            'logs': logs_data
        }), 200
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error getting product audit logs: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500