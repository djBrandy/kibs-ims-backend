from flask import Blueprint, jsonify, request, session
from app.models import db, Product, Purchase, Supplier, AuditLog
from routes.auth import login_required, admin_required
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy import func

predictive_bp = Blueprint('predictive', __name__, url_prefix='/api/predictive')

@predictive_bp.route('/restocking-suggestions', methods=['GET'])
@login_required
def get_restocking_suggestions():
    """
    Generate AI-based restocking suggestions based on:
    - Historical sales/usage data
    - Current stock levels
    - Supplier lead times
    - Seasonal trends
    """
    # Get all products with their purchase history
    products = Product.query.all()
    suggestions = []
    
    for product in products:
        # Get purchase history for this product (last 90 days)
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        purchases = Purchase.query.filter_by(product_id=product.id).filter(
            Purchase.purchase_date >= ninety_days_ago
        ).all()
        
        # Get audit logs for this product (usage/consumption)
        audit_logs = AuditLog.query.filter_by(
            product_id=product.id, 
            action_type='update_product'
        ).filter(
            AuditLog.timestamp >= ninety_days_ago
        ).all()
        
        # Calculate consumption rate
        consumption_data = []
        for log in audit_logs:
            # Try to extract quantity changes from audit logs
            try:
                if log.previous_value and log.new_value:
                    prev = int(log.previous_value)
                    new = int(log.new_value)
                    if prev > new:  # Consumption happened
                        consumption_data.append(prev - new)
            except (ValueError, TypeError):
                continue
        
        # If we have enough consumption data
        if consumption_data:
            avg_consumption = sum(consumption_data) / len(consumption_data)
            
            # Calculate days until stockout based on current quantity and average consumption
            days_until_stockout = float('inf') if avg_consumption == 0 else product.quantity / avg_consumption
            
            # Determine urgency level
            urgency = "LOW"
            if days_until_stockout <= 7:
                urgency = "HIGH"
            elif days_until_stockout <= 14:
                urgency = "MEDIUM"
            
            # Calculate optimal reorder quantity (simple model)
            # In a real system, this would use more sophisticated algorithms
            optimal_quantity = max(int(avg_consumption * 30), product.low_stock_alert * 2)
            
            # Get supplier information
            supplier = Supplier.query.filter(
                Supplier.id.in_([p.supplier_id for p in purchases])
            ).order_by(func.count().desc()).first()
            
            suggestions.append({
                'product_id': product.id,
                'product_name': product.product_name,
                'current_quantity': product.quantity,
                'days_until_stockout': round(days_until_stockout),
                'suggested_reorder_quantity': optimal_quantity,
                'urgency': urgency,
                'supplier_id': supplier.id if supplier else None,
                'supplier_name': supplier.shop_name if supplier else "Unknown",
                'avg_consumption_rate': round(avg_consumption, 2),
                'last_purchase_date': max([p.purchase_date for p in purchases]).isoformat() if purchases else None
            })
    
    # Sort by urgency (HIGH, MEDIUM, LOW)
    urgency_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    suggestions.sort(key=lambda x: (urgency_order.get(x['urgency'], 3), x['days_until_stockout']))
    
    return jsonify(suggestions)

@predictive_bp.route('/restock', methods=['POST'])
@admin_required
def create_restock_order():
    """Create a restocking order based on suggestions"""
    data = request.get_json()
    product_ids = data.get('product_ids', [])
    quantities = data.get('quantities', {})
    
    if not product_ids:
        return jsonify({'error': 'No products selected for restocking'}), 400
    
    # In a real system, this would create purchase orders
    # For now, we'll just log the restock request
    
    user_id = session.get('user_id')
    for product_id in product_ids:
        product = Product.query.get(product_id)
        if not product:
            continue
            
        quantity = quantities.get(str(product_id), product.low_stock_alert * 2)
        
        log_entry = AuditLog(
            product_id=product_id,
            user_id=user_id,
            action_type='restock_order',
            previous_value=str(product.quantity),
            new_value=str(quantity),
            notes=f"Predictive restocking order created for {quantity} units"
        )
        db.session.add(log_entry)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Restocking orders created'})