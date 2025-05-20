from flask import Blueprint, jsonify # type: ignore
from app import db 
from app.models import Product, Purchase, AlertNotification, Supplier 
from routes.auth import login_required
import traceback
from sqlalchemy import desc # type: ignore

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

@alerts_bp.route('/', methods=['GET'])
@login_required
def get_alerts():
    try:
        from datetime import datetime, timedelta 
        today = datetime.now().date()
        expiration_threshold = today + timedelta(days=3)
        
        print(f"Current date: {today}, Expiration threshold: {expiration_threshold}")
        

        low_stock_products = Product.query.filter(
            Product.quantity <= Product.low_stock_alert,
            Product.quantity > 0  
        ).all()
        
        print(f"Found {len(low_stock_products)} products with low stock")
        
        

        expiring_products = Product.query.filter(
            Product.expiration_date.isnot(None),
            Product.expiration_date <= expiration_threshold,
            Product.expiration_date >= today,
            Product.checkbox_expiry_date == True
        ).all()
        
       
        
        alerts = []
        
       
        for product in low_stock_products:
            
            
            
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
        
        

        for product in expiring_products:
            
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
        error_details = traceback.format_exc()
        
        
        return jsonify({'error': str(e)}), 500


@alerts_bp.route('/send-notifications', methods=['POST'])
@login_required
def send_notifications():
    try:
        
        from datetime import datetime, timedelta
        now = datetime.now()
        six_hours_ago = now - timedelta(hours=6)
        today = now.date()
        expiration_threshold = today + timedelta(days=3)
        
        
        low_stock_products = Product.query.filter(
            Product.quantity <= Product.low_stock_alert,
            Product.quantity > 0  
            
        ).all()
        
        

        expiring_products = Product.query.filter(
            Product.expiration_date.isnot(None),
            Product.expiration_date <= expiration_threshold,
            Product.expiration_date >= today,  
            Product.checkbox_expiry_date == True  
        ).all()
        
        notifications_sent = 0
        
        
        for product in low_stock_products:
            
            
            alert = AlertNotification.query.filter_by(
                product_id=product.id,
                alert_type='low_stock',
                resolved=False
            ).first()
            


            # FUNCTION TO SEND THE SMS
            # Check if we've already sent a notification in the last 6 hours
            if not alert or alert.last_notified < six_hours_ago:
                
                
                message = f"LOW STOCK ALERT: {product.product_name} is running low. Current quantity: {product.quantity} {product.unit_of_measure}. Threshold: {product.low_stock_alert} {product.unit_of_measure}."
                send_sms("+254112607179", message)
                
                
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
        

        
        
        for product in expiring_products:
            
            
            alert = AlertNotification.query.filter_by(
                product_id=product.id,
                alert_type='expiration',
                resolved=False
            ).first()
            
            if not alert or alert.last_notified < six_hours_ago:
                days_until_expiry = (product.expiration_date - today).days
                
                
                message = f"EXPIRATION ALERT: {product.product_name} will expire in {days_until_expiry} days (on {product.expiration_date.isoformat()})."
                send_sms("+254112607179", message)
                
                
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
        error_details = traceback.format_exc()
        print(f"Error in send_notifications: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e)}), 500



# CONTINUED FUNCTION TO SEND SMS
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