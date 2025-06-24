from flask import Blueprint, request, jsonify, session # type: ignore
from app.database import db
from app.models import Product, AuditLog, Worker 
from datetime import datetime, timedelta
from routes.auth import login_required
import traceback
import requests

audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit')

@audit_bp.route('/scan/<barcode>', methods=['GET'])
@login_required
def scan_product(barcode):
    try:
        print(f"Searching for product with QR code: {barcode}")
        
        product = Product.query.filter_by(qr_code=barcode).first()
        
        if not product:
            print("Product not found with direct match, trying string conversion")
            product = Product.query.filter(Product.qr_code == str(barcode)).first()
            
        if not product:
            print("Product not found with string conversion, trying numeric conversion")
            try:
                numeric_barcode = int(barcode)
                product = Product.query.filter(Product.qr_code == str(numeric_barcode)).first()
            except (ValueError, TypeError):
                pass
        if not product:
            print("Product not found after all conversion attempts")
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
            'special_instructions': product.special_instructions,
            'product_type': product.product_type  # Add product_type to the response
        }), 200
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error in scan_product: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500

@audit_bp.route('/update/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        print(f"Updating product {product_id}: {data}")
        
        previous_quantity = product.quantity
        previous_concentration = product.concentration
        previous_instructions = product.special_instructions
        
        # Define special product types that require special auditing
        special_audit_types = ['Equipment', 'Reference Material', 'Protective Equipment', 'Data Storage Devices', 'Lab Furniture']
        
        if 'quantity' in data:
            # For Equipment, focus on working status instead of quantity
            if product.product_type.lower() == 'equipment':
                working_status = data.get('notes', '')
                is_not_working = 'not working' in working_status.lower()
                
                audit_log = AuditLog(
                    product_id=product.id,
                    user_id=session.get('user_id'),
                    action_type='equipment_status_update',
                    previous_value=previous_instructions or 'Unknown',
                    new_value=working_status,
                    notes=f"Equipment status: {'working' if 'working' in working_status.lower() else 'not working' if is_not_working else working_status}"
                )
                db.session.add(audit_log)
                product.special_instructions = working_status
                print(f"Updated equipment status: {working_status}")
                
                # If equipment is not working, flag for AI diagnostics
                if is_not_working:
                    # Create a diagnostic flag in the audit log
                    diagnostic_flag = AuditLog(
                        product_id=product.id,
                        user_id=session.get('user_id'),
                        action_type='diagnostic_needed',
                        previous_value='equipment_working',
                        new_value='equipment_not_working',
                        notes=f"AI diagnostic needed for {product.product_name}"
                    )
                    db.session.add(diagnostic_flag)
            # For other special product types, still track quantity but with special audit type
            elif product.product_type in special_audit_types:
                try:
                    new_quantity = int(data['quantity'])
                    if new_quantity != previous_quantity:
                        audit_log = AuditLog(
                            product_id=product.id,
                            user_id=session.get('user_id'),
                            action_type=f"{product.product_type.lower().replace(' ', '_')}_update",
                            previous_value=str(previous_quantity),
                            new_value=str(new_quantity),
                            notes=data.get('notes', f'{product.product_type} updated')
                        )
                        db.session.add(audit_log)
                        product.quantity = new_quantity
                        print(f"Updated {product.product_type} quantity from {previous_quantity} to {new_quantity}")
                except (ValueError, TypeError) as e:
                    return jsonify({'error': f'Invalid quantity value: {str(e)}'}), 400
            # For regular products, use the standard quantity update
            else:
                try:
                    new_quantity = int(data['quantity'])
                    if new_quantity != previous_quantity:
                        audit_log = AuditLog(
                            product_id=product.id,
                            user_id=session.get('user_id'),
                            action_type='quantity_update',
                            previous_value=str(previous_quantity),
                            new_value=str(new_quantity),
                            notes=data.get('notes', 'Quantity updated')
                        )
                        db.session.add(audit_log)
                        product.quantity = new_quantity
                        print(f"Updated quantity from {previous_quantity} to {new_quantity}")
                except (ValueError, TypeError) as e:
                    return jsonify({'error': f'Invalid quantity value: {str(e)}'}), 400
        if 'concentration' in data:
            try:
                if data['concentration'] and str(data['concentration']).strip():
                    new_concentration = float(data['concentration'])
                    if new_concentration != previous_concentration:
                        audit_log = AuditLog(
                            product_id=product.id,
                            user_id=session.get('user_id'),
                            action_type='concentration_update',
                            previous_value=str(previous_concentration) if previous_concentration is not None else 'None',
                            new_value=str(new_concentration),
                            notes=data.get('notes', 'Concentration updated')
                        )
                        db.session.add(audit_log)
                        product.concentration = new_concentration
                        print(f"Updated concentration from {previous_concentration} to {new_concentration}")
                else:
                    if previous_concentration is not None:
                        audit_log = AuditLog(
                            product_id=product.id,
                            user_id=session.get('user_id'),
                            action_type='concentration_update',
                            previous_value=str(previous_concentration) if previous_concentration is not None else 'None',
                            new_value='None',
                            notes=data.get('notes', 'Concentration cleared')
                        )
                        db.session.add(audit_log)
                        product.concentration = None
                        print(f"Cleared concentration (was {previous_concentration})")
            except (ValueError, TypeError) as e:
                return jsonify({'error': f'Invalid concentration value: {str(e)}'}), 400
        if 'special_instructions' in data and data['special_instructions'] != product.special_instructions:
            audit_log = AuditLog(
                product_id=product.id,
                user_id=session.get('user_id'),
                action_type='notes_update',
                previous_value=previous_instructions if previous_instructions else 'None',
                new_value=data['special_instructions'] if data['special_instructions'] else 'None',
                notes=data.get('notes', 'Special instructions updated')
            )
            db.session.add(audit_log)
            product.special_instructions = data['special_instructions']
            print(f"Updated special instructions from '{previous_instructions}' to '{data['special_instructions']}'")
        
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
    try:
        product_id = request.args.get('product_id', type=int)
        action_type = request.args.get('action_type')
        days = request.args.get('days', type=int)
        limit = request.args.get('limit', 100, type=int)
        
        query = AuditLog.query
        
        if product_id:
            query = query.filter(AuditLog.product_id == product_id)
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = query.filter(AuditLog.timestamp >= cutoff_date)
        
        query = query.order_by(AuditLog.timestamp.desc())
        query = query.limit(limit)
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
        from flask import send_file # type: ignore
        import tempfile
        from reportlab.lib.pagesizes import letter # type: ignore
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer # type: ignore
        from reportlab.lib.styles import getSampleStyleSheet # type: ignore
        from reportlab.lib import colors # type: ignore
        
        product_id = request.args.get('product_id', type=int)
        action_type = request.args.get('action_type')
        days = request.args.get('days', type=int)
        
        query = AuditLog.query.join(Product, AuditLog.product_id == Product.id)
        
        if product_id:
            query = query.filter(AuditLog.product_id == product_id)
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = query.filter(AuditLog.timestamp >= cutoff_date)
        
        query = query.order_by(AuditLog.timestamp.desc())
        logs = query.all()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
        
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        title = Paragraph("Audit Logs Report", styles['Heading1'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        
        date_text = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        elements.append(date_text)
        elements.append(Spacer(1, 20))
        
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
        
        table = Table(data)
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
        elements.append(table)
        doc.build(elements)
        
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
    try:
        limit = request.args.get('limit', 50, type=int)
        include_ai_diagnostics = request.args.get('include_ai_diagnostics', 'true').lower() == 'true'
        product = Product.query.get_or_404(product_id)
        
        query = AuditLog.query.filter_by(product_id=product_id)
        
        # Filter by action type if specified
        action_type = request.args.get('action_type')
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)
        
        # Special handling for AI diagnostics
        if include_ai_diagnostics:
            # Include AI diagnostic logs
            query = query.order_by(AuditLog.timestamp.desc())
        else:
            # Exclude AI diagnostic logs
            query = query.filter(~AuditLog.action_type.in_(['ai_diagnostic_started', 'ai_diagnosis']))
            query = query.order_by(AuditLog.timestamp.desc())
        
        logs = query.limit(limit).all()
        
        logs_data = []
        for log in logs:
            log_dict = log.to_dict() if hasattr(log, "to_dict") else {
                "id": log.id,
                "timestamp": log.timestamp,
                "action_type": log.action_type,
                "previous_value": log.previous_value,
                "new_value": log.new_value,
                "notes": log.notes,
                "user_id": log.user_id,
            }
            
            # Format AI diagnosis logs specially
            if log.action_type == 'ai_diagnosis':
                log_dict["is_ai_diagnosis"] = True
                log_dict["diagnosis_summary"] = log.notes
            
            # Fetch worker username if user_id is present
            worker_username = None
            if log.user_id:
                worker = Worker.query.get(log.user_id)
                if worker:
                    worker_username = worker.username
            log_dict["worker_username"] = worker_username
            logs_data.append(log_dict)

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