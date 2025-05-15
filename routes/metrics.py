from flask import Blueprint, jsonify, request
from app import db
from app import Product
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import json

metrics_bp = Blueprint('metrics', __name__, url_prefix='/api/metrics')

@metrics_bp.route('/', methods=['GET'])
def get_performance_metrics():
    try:
        # Calculate inventory stock worth (sum of price * quantity for all products)
        inventory_worth = db.session.query(func.sum(Product.price_in_kshs * Product.quantity)).scalar() or 0
        
        # Count number of audits (placeholder - would need an audit log table)
        # For now, we'll use a mock value
        audit_count = 24
        
        # Get new products (added in the last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_products = Product.query.filter(Product.date_of_entry >= thirty_days_ago).count()
        
        # Get supplier count (unique manufacturers)
        supplier_count = db.session.query(func.count(func.distinct(Product.manufacturer))).scalar() or 0
        
        # Calculate inventory turnover (mock calculation)
        # In a real implementation, this would be: COGS / Average Inventory Value
        inventory_turnover = 3.2
        
        # Calculate average order value (mock data)
        avg_order_value = 122
        
        # Calculate changes (mock data for demonstration)
        # In a real app, you would compare with previous period
        inventory_worth_change = 8.3
        audit_count_change = 4
        inventory_turnover_change = 0.4
        new_products_change = 3
        supplier_count_change = 2
        avg_order_value_change = 7
        
        return jsonify({
            "inventoryWorth": {
                "value": float(inventory_worth),
                "change": inventory_worth_change
            },
            "auditCount": {
                "value": audit_count,
                "change": audit_count_change
            },
            "inventoryTurnover": {
                "value": inventory_turnover,
                "change": inventory_turnover_change
            },
            "newProducts": {
                "value": new_products,
                "change": new_products_change
            },
            "supplierCount": {
                "value": supplier_count,
                "change": supplier_count_change
            },
            "avgOrderValue": {
                "value": float(avg_order_value),
                "change": avg_order_value_change
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metrics_bp.route('/chart/<metric_type>', methods=['GET'])
def get_metric_chart_data(metric_type):
    try:
        # Get time range from query parameters (default to 'month')
        time_range = request.args.get('range', 'month')
        
        # Define time periods based on range
        if time_range == 'day':
            # Hourly data for the past 24 hours
            periods = 24
            period_format = '%H:00'
            delta = timedelta(hours=1)
            start_time = datetime.now() - timedelta(days=1)
        elif time_range == 'week':
            # Daily data for the past 7 days
            periods = 7
            period_format = '%a'
            delta = timedelta(days=1)
            start_time = datetime.now() - timedelta(days=7)
        elif time_range == 'year':
            # Monthly data for the past 12 months
            periods = 12
            period_format = '%b'
            delta = timedelta(days=30)
            start_time = datetime.now() - timedelta(days=365)
        else:  # month (default)
            # Daily data for the past 30 days
            periods = 30
            period_format = '%d %b'
            delta = timedelta(days=1)
            start_time = datetime.now() - timedelta(days=30)
        
        # Generate mock data based on metric type
        labels = []
        data = []
        
        current_time = start_time
        for i in range(periods):
            labels.append(current_time.strftime(period_format))
            
            # Generate different data patterns based on metric type
            if metric_type == 'inventoryWorth':
                base_value = 10000
                variation = 2000 * (0.5 + (i / periods))
                data.append(base_value + variation)
            elif metric_type == 'auditCount':
                data.append(1 if i % 3 == 0 else 0)  # Audits every 3 periods
            elif metric_type == 'inventoryTurnover':
                data.append(3.0 + (i * 0.05))  # Gradually increasing turnover
            elif metric_type == 'newProducts':
                data.append(2 if i % 4 == 0 else 0)  # New products added periodically
            elif metric_type == 'supplierCount':
                # Supplier count occasionally increases
                data.append(20 + (1 if i % 10 == 0 and i > 0 else 0))
            elif metric_type == 'avgOrderValue':
                base_value = 120
                variation = 20 * (0.5 + (i / periods))
                data.append(base_value + variation)
            
            current_time += delta
        
        return jsonify({
            'labels': labels,
            'data': data,
            'metric': metric_type,
            'timeRange': time_range
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500