from flask import Blueprint, jsonify
from app import db, Product, Purchase, AlertNotification, Supplier
from datetime import datetime, timedelta
import requests
import os
from sqlalchemy import desc

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

@alerts_bp.route('/', methods=['GET'])
def get_alerts():
    try:
        # Get current date
        today = datetime.now().date()
        expiration_threshold = today + timedelta(days=3)
        
        # Get products with low stock
        low_stock_products = Product.query.filter(Product.quantity <= Product.low_stock_alert).all()
        
        # Get products near expiration
        expiring_products = Product.query.filter(
            Product.expiration_date.isnot(None),
            Product.expiration_date <= expiration_threshold
        ).all()
        
        # Combine alerts
        alerts = []
        
        # Process low stock alerts
        for product in low_stock_products:
            # Get the latest purchase for this product
            latest_purchase = Purchase.query.filter_by(product_id=product.id).order_by(desc(Purchase.purchase_date)).first()
            
            supplier_name = None
            last_purchase_price = None
            last_purchase_date = None
            
            if latest_purchase:
                supplier = Supplier.query.get(latest_purchase.supplier_id)
                supplier_name = supplier.shop_name if supplier else None
                last_purchase_price = latest_purchase.price_per_unit
                last_purchase_date = latest_purchase.purchase_date
            
            alerts.append({
                'id': product.id,
                'product_name': product.product_name,
                'alert_type': 'low_stock',
                'current_quantity': product.quantity,
                'threshold': product.low_stock_alert,
                'unit_of_measure': product.unit_of_measure,
                'supplier_name': supplier_name,
                'last_purchase_price': last_purchase_price,
                'last_purchase_date': last_purchase_date.isoformat() if last_purchase_date else None
            })
        
        # Process expiration alerts
        for product in expiring_products:
            # Get the latest purchase for this product
            latest_purchase = Purchase.query.filter_by(product_id=product.id).order_by(desc(Purchase.purchase_date)).first()
            
            supplier_name = None
            last_purchase_price = None
            last_purchase_date = None
            
            if latest_purchase:
                supplier = Supplier.query.get(latest_purchase.supplier_id)
                supplier_name = supplier.shop_name if supplier else None
                last_purchase_price = latest_purchase.price_per_unit
                last_purchase_date = latest_purchase.purchase_date
            
            days_until_expiry = (product.expiration_date - today).days
            
            alerts.append({
                'id': product.id,
                'product_name': product.product_name,
                'alert_type': 'expiration',
                'expiration_date': product.expiration_date.isoformat(),
                'days_until_expiry': days_until_expiry,
                'supplier_name': supplier_name,
                'last_purchase_price': last_purchase_price,
                'last_purchase_date': last_purchase_date.isoformat() if last_purchase_date else None
            })
        
        return jsonify(alerts), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@alerts_bp.route('/send-notifications', methods=['POST'])
def send_notifications():
    try:
        # Get current date and time
        now = datetime.now()
        six_hours_ago = now - timedelta(hours=6)
        today = now.date()
        expiration_threshold = today + timedelta(days=3)
        
        # Get products with low stock
        low_stock_products = Product.query.filter(Product.quantity <= Product.low_stock_alert).all()
        
        # Get products near expiration
        expiring_products = Product.query.filter(
            Product.expiration_date.isnot(None),
            Product.expiration_date <= expiration_threshold
        ).all()
        
        notifications_sent = 0
        
        # Process low stock alerts
        for product in low_stock_products:
            # Check if we've already sent a notification in the last 6 hours
            alert = AlertNotification.query.filter_by(
                product_id=product.id,
                alert_type='low_stock',
                resolved=False
            ).first()
            
            if not alert or alert.last_notified < six_hours_ago:
                # Send SMS notification
                message = f"LOW STOCK ALERT: {product.product_name} is running low. Current quantity: {product.quantity} {product.unit_of_measure}. Threshold: {product.low_stock_alert} {product.unit_of_measure}."
                send_sms("+254112607179", message)
                
                # Update or create notification record
                if alert:
                    alert.last_notified = now
                else:
                    alert = AlertNotification(
                        product_id=product.id,
                        alert_type='low_stock',
                        last_notified=now
                    )
                    db.session.add(alert)
                
                notifications_sent += 1
        
        # Process expiration alerts
        for product in expiring_products:
            # Check if we've already sent a notification in the last 6 hours
            alert = AlertNotification.query.filter_by(
                product_id=product.id,
                alert_type='expiration',
                resolved=False
            ).first()
            
            if not alert or alert.last_notified < six_hours_ago:
                days_until_expiry = (product.expiration_date - today).days
                
                # Send SMS notification
                message = f"EXPIRATION ALERT: {product.product_name} will expire in {days_until_expiry} days (on {product.expiration_date.isoformat()})."
                send_sms("+254112607179", message)
                
                # Update or create notification record
                if alert:
                    alert.last_notified = now
                else:
                    alert = AlertNotification(
                        product_id=product.id,
                        alert_type='expiration',
                        last_notified=now
                    )
                    db.session.add(alert)
                
                notifications_sent += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'notifications_sent': notifications_sent
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def send_sms(phone_number, message):
    """
    Send SMS using Africa's Talking API
    You'll need to set up an account and get API credentials
    """
    try:
        # This is a placeholder - you'll need to implement actual SMS sending
        # using a service like Africa's Talking, Twilio, etc.
        print(f"Sending SMS to {phone_number}: {message}")
        
        # Example using Africa's Talking (you would need to install the package)
        # import africastalking
        # username = "your_username"
        # api_key = "your_api_key"
        # africastalking.initialize(username, api_key)
        # sms = africastalking.SMS
        # response = sms.send(message, [phone_number])
        
        # For now, just log the message
        return True
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        return False