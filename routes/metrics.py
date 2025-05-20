from flask import Blueprint, jsonify, request # type: ignore
from app import db
from app.models import Product, Purchase, Supplier, AuditLog 

from sqlalchemy import func, desc # type: ignore
from datetime import datetime, timedelta
from routes.auth import login_required
import json

metrics_bp = Blueprint('metrics', __name__, url_prefix='/api/metrics')

@metrics_bp.route('/', methods=['GET'])
@login_required
def get_performance_metrics():
    try:
        inventory_worth = db.session.query(func.sum(Product.price_in_kshs * Product.quantity)).scalar() or 0
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        sixty_days_ago = datetime.now() - timedelta(days=60)
        
        audit_count = AuditLog.query.filter(
            AuditLog.timestamp >= thirty_days_ago
        ).count()
        previous_audit_count = AuditLog.query.filter(
            AuditLog.timestamp >= sixty_days_ago,
            AuditLog.timestamp < thirty_days_ago
        ).count()
        new_products = Product.query.filter(Product.date_of_entry >= thirty_days_ago).count()
        supplier_count = db.session.query(func.count(func.distinct(Product.manufacturer))).scalar() or 0
        
        total_purchases = db.session.query(func.sum(Purchase.total_price)).filter(
            Purchase.purchase_date >= thirty_days_ago
        ).scalar() or 0
        
        avg_inventory_value = inventory_worth / 2
        inventory_turnover = total_purchases / avg_inventory_value if avg_inventory_value > 0 else 0
        
        recent_purchases = Purchase.query.filter(Purchase.purchase_date >= thirty_days_ago).all()
        if recent_purchases:
            avg_order_value = sum(p.total_price for p in recent_purchases) / len(recent_purchases)
        else:
            avg_order_value = 0
        
        previous_inventory_worth = db.session.query(
            func.sum(Product.price_in_kshs * Product.quantity)
        ).filter(
            Product.date_of_entry < thirty_days_ago
        ).scalar() or 0
        if previous_inventory_worth > 0:
            inventory_worth_change = ((inventory_worth - previous_inventory_worth) / previous_inventory_worth) * 100
        else:
            inventory_worth_change = 0
        
        audit_count_change = audit_count - previous_audit_count
        
        previous_purchases = db.session.query(func.sum(Purchase.total_price)).filter(
            Purchase.purchase_date >= sixty_days_ago,
            Purchase.purchase_date < thirty_days_ago
        ).scalar() or 0
        
        previous_inventory_turnover = previous_purchases / avg_inventory_value if avg_inventory_value > 0 else 0
        inventory_turnover_change = inventory_turnover - previous_inventory_turnover
        
        previous_new_products = Product.query.filter(
            Product.date_of_entry >= sixty_days_ago,
            Product.date_of_entry < thirty_days_ago
        ).count()
        new_products_change = new_products - previous_new_products
        
        previous_supplier_count = Supplier.query.filter(
            Supplier.created_at < thirty_days_ago
        ).count()
        supplier_count_change = supplier_count - previous_supplier_count
        
        previous_period_purchases = Purchase.query.filter(
            Purchase.purchase_date >= sixty_days_ago,
            Purchase.purchase_date < thirty_days_ago
        ).all()
        
        if previous_period_purchases:
            previous_avg_order_value = sum(p.total_price for p in previous_period_purchases) / len(previous_period_purchases)
            avg_order_value_change = ((avg_order_value - previous_avg_order_value) / previous_avg_order_value) * 100 if previous_avg_order_value > 0 else 0
        else:
            avg_order_value_change = 0
        
        return jsonify({
            "inventoryWorth": {
                "value": float(inventory_worth),
                "change": round(float(inventory_worth_change), 1)
            },
            "auditCount": {
                "value": audit_count,
                "change": audit_count_change
            },
            "inventoryTurnover": {
                "value": round(float(inventory_turnover), 1) if inventory_turnover else 0,
                "change": round(float(inventory_turnover_change), 1)
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
                "value": round(float(avg_order_value), 2),
                "change": round(float(avg_order_value_change), 1)
            }
        }), 200
        
    except Exception as e:
        # print(f"Error in get_performance_metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@metrics_bp.route('/chart/<metric_type>', methods=['GET'])
@login_required
def get_metric_chart_data(metric_type):
    try:
        time_range = request.args.get('range', 'month')
        
        if time_range == 'day':
            periods = 24
            period_format = '%H:00'
            delta = timedelta(hours=1)
            start_time = datetime.now() - timedelta(days=1)
        elif time_range == 'week':
            periods = 7
            period_format = '%a'
            delta = timedelta(days=1)
            start_time = datetime.now() - timedelta(days=7)
        elif time_range == 'year':
            periods = 12
            period_format = '%b'
            delta = timedelta(days=30)
            start_time = datetime.now() - timedelta(days=365)
        else:
            periods = 30
            period_format = '%d %b'
            delta = timedelta(days=1)
            start_time = datetime.now() - timedelta(days=30)
        
        labels = []
        data = []
        
        if metric_type == 'auditCount':
            current_time = start_time
            for i in range(periods):
                period_end = current_time + delta
                labels.append(current_time.strftime(period_format))
                count = AuditLog.query.filter(
                    AuditLog.timestamp >= current_time,
                    AuditLog.timestamp < period_end
                ).count()
                data.append(count)
                current_time = period_end
        else:
            current_time = start_time
            for i in range(periods):
                labels.append(current_time.strftime(period_format))
                if metric_type == 'inventoryWorth':
                    base_value = 10000
                    variation = 2000 * (0.5 + (i / periods))
                    data.append(base_value + variation)
                elif metric_type == 'inventoryTurnover':
                    data.append(3.0 + (i * 0.05)) 
                    
                elif metric_type == 'newProducts':
                    data.append(2 if i % 4 == 0 else 0)  
                    
                elif metric_type == 'supplierCount':
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
        # print(f"Error in get_metric_chart_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@metrics_bp.route('/audit-logs', methods=['GET'])
@login_required
def get_audit_logs():
    try:
        limit = request.args.get('limit', 10, type=int)
        product_id = request.args.get('product_id', type=int)
        action_type = request.args.get('action_type')
        days = request.args.get('days', type=int)
        
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
        logs = query.all()
        
        result = []
        for log in logs:
            log_dict = log.to_dict()
            if log.timestamp:
                log_dict['date'] = log.timestamp.strftime('%Y-%m-%d')
                log_dict['time'] = log.timestamp.strftime('%H:%M:%S')
            result.append(log_dict)
        
        return jsonify(result), 200
    
    except Exception as e:
        # print(f"Error in get_audit_logs: {str(e)}")
        return jsonify({'error': str(e)}), 500