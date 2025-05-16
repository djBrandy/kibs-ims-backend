from flask import Blueprint, jsonify, request
from app import db, Product, Purchase
from datetime import datetime, timedelta
from routes.auth import login_required
from sqlalchemy import func, desc, case
import traceback

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/update', methods=['POST'])
@login_required
def update_analytics():
    """Update inventory analytics data"""
    try:
        from app import InventoryAnalytics, AuditLog, Product
        from sqlalchemy import func
        
        # Get all products
        products = Product.query.all()
        
        for product in products:
            # Find the last audit log for this product that changed quantity
            last_movement = AuditLog.query.filter(
                AuditLog.product_id == product.id,
                AuditLog.action_type == 'quantity_update'
            ).order_by(AuditLog.timestamp.desc()).first()
            
            # Calculate days without movement
            days_without_movement = None
            last_movement_date = None
            if last_movement:
                last_movement_date = last_movement.timestamp
                days_without_movement = (datetime.now() - last_movement_date).days
            
            # Count stockouts (when quantity was set to 0)
            stockout_logs = AuditLog.query.filter(
                AuditLog.product_id == product.id,
                AuditLog.action_type == 'quantity_update',
                AuditLog.new_value == '0'
            ).all()
            
            stockout_count = len(stockout_logs)
            last_stockout_date = stockout_logs[0].timestamp if stockout_logs else None
            
            # Determine if it's dead stock (no movement in 90+ days)
            is_dead_stock = days_without_movement >= 90 if days_without_movement else False
            
            # Determine if it's slow-moving (no movement in 30-90 days)
            is_slow_moving = (days_without_movement >= 30 and days_without_movement < 90) if days_without_movement else False
            
            # Check if analytics record exists for this product
            analytics = InventoryAnalytics.query.filter_by(product_id=product.id).first()
            
            if analytics:
                # Update existing record
                analytics.last_movement_date = last_movement_date
                analytics.days_without_movement = days_without_movement
                analytics.stockout_count = stockout_count
                analytics.last_stockout_date = last_stockout_date
                analytics.is_dead_stock = is_dead_stock
                analytics.is_slow_moving = is_slow_moving
                analytics.last_updated = datetime.now()
            else:
                # Create new record
                analytics = InventoryAnalytics(
                    product_id=product.id,
                    last_movement_date=last_movement_date,
                    days_without_movement=days_without_movement,
                    stockout_count=stockout_count,
                    last_stockout_date=last_stockout_date,
                    is_dead_stock=is_dead_stock,
                    is_slow_moving=is_slow_moving
                )
                db.session.add(analytics)
        
        # Calculate movement ranks based on frequency of quantity updates
        movement_counts = db.session.query(
            AuditLog.product_id,
            func.count(AuditLog.id).label('movement_count')
        ).filter(
            AuditLog.action_type == 'quantity_update'
        ).group_by(
            AuditLog.product_id
        ).order_by(
            func.count(AuditLog.id).desc()
        ).all()
        
        # Update movement ranks
        for rank, (product_id, _) in enumerate(movement_counts, 1):
            analytics = InventoryAnalytics.query.filter_by(product_id=product_id).first()
            if analytics:
                analytics.movement_rank = rank
                analytics.is_top_product = rank <= 5  # Top 5 products
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Analytics updated successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        error_details = traceback.format_exc()
        print(f"Error updating analytics: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/stockout', methods=['GET'])
@login_required
def get_stockout_data():
    """Get stockout rate data"""
    try:
        from app import InventoryAnalytics, Product
        
        # Get products with stockout data
        stockout_data = db.session.query(
            InventoryAnalytics, Product
        ).join(
            Product, InventoryAnalytics.product_id == Product.id
        ).filter(
            InventoryAnalytics.stockout_count > 0
        ).order_by(
            InventoryAnalytics.stockout_count.desc()
        ).all()
        
        result = []
        for analytics, product in stockout_data:
            result.append({
                'product_id': product.id,
                'product_name': product.product_name,
                'stockout_count': analytics.stockout_count,
                'last_stockout_date': analytics.last_stockout_date.isoformat() if analytics.last_stockout_date else None
            })
        
        return jsonify(result), 200
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error getting stockout data: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/dead-stock', methods=['GET'])
@login_required
def get_dead_stock():
    """Get dead stock items (no movement in 90 days)"""
    try:
        from app import InventoryAnalytics, Product
        
        # Get dead stock items
        dead_stock = db.session.query(
            InventoryAnalytics, Product
        ).join(
            Product, InventoryAnalytics.product_id == Product.id
        ).filter(
            InventoryAnalytics.is_dead_stock == True
        ).order_by(
            InventoryAnalytics.days_without_movement.desc()
        ).all()
        
        result = []
        for analytics, product in dead_stock:
            result.append({
                'product_id': product.id,
                'product_name': product.product_name,
                'days_without_movement': analytics.days_without_movement,
                'last_movement_date': analytics.last_movement_date.isoformat() if analytics.last_movement_date else None,
                'current_quantity': product.quantity,
                'unit_of_measure': product.unit_of_measure
            })
        
        return jsonify(result), 200
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error getting dead stock data: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/top-products', methods=['GET'])
@login_required
def get_top_products():
    """Get top-moving products"""
    try:
        from app import InventoryAnalytics, Product
        
        # Get top products by movement rank
        top_products = db.session.query(
            InventoryAnalytics, Product
        ).join(
            Product, InventoryAnalytics.product_id == Product.id
        ).filter(
            InventoryAnalytics.is_top_product == True
        ).order_by(
            InventoryAnalytics.movement_rank
        ).all()
        
        result = []
        for analytics, product in top_products:
            result.append({
                'product_id': product.id,
                'product_name': product.product_name,
                'movement_rank': analytics.movement_rank,
                'current_quantity': product.quantity,
                'unit_of_measure': product.unit_of_measure
            })
        
        return jsonify(result), 200
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error getting top products data: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/slow-moving', methods=['GET'])
@login_required
def get_slow_moving():
    """Get slow-moving items (no movement in 30 days but less than 90)"""
    try:
        from app import InventoryAnalytics, Product
        
        # Get slow-moving items
        slow_moving = db.session.query(
            InventoryAnalytics, Product
        ).join(
            Product, InventoryAnalytics.product_id == Product.id
        ).filter(
            InventoryAnalytics.is_slow_moving == True
        ).order_by(
            InventoryAnalytics.days_without_movement.desc()
        ).all()
        
        result = []
        for analytics, product in slow_moving:
            result.append({
                'product_id': product.id,
                'product_name': product.product_name,
                'days_without_movement': analytics.days_without_movement,
                'last_movement_date': analytics.last_movement_date.isoformat() if analytics.last_movement_date else None,
                'current_quantity': product.quantity,
                'unit_of_measure': product.unit_of_measure
            })
        
        return jsonify(result), 200
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error getting slow-moving data: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500