from app import db, Product, Purchase, Supplier, AlertNotification
from datetime import datetime, timedelta
import random

def create_test_data():
    """Create test data for alerts functionality"""
    print("Creating test data for alerts...")
    
    # Get or create a test supplier
    supplier = Supplier.query.first()
    if not supplier:
        supplier = Supplier(
            shop_name="Test Supplier",
            primary_contact="Contact Person",
            phone="123456789",
            email="supplier@example.com",
            address="123 Test Street"
        )
        db.session.add(supplier)
        db.session.commit()
        print(f"Created test supplier: {supplier.shop_name}")
    
    # Get some products to modify
    products = Product.query.limit(5).all()
    
    if not products:
        print("No products found in database. Please add some products first.")
        return
    
    modified_count = 0
    
    # Set some products to low stock
    for i, product in enumerate(products):
        if i % 2 == 0:  # Every other product
            # Set low stock
            product.quantity = max(0, product.low_stock_alert - random.randint(1, 5))
            print(f"Set {product.product_name} to low stock: {product.quantity}/{product.low_stock_alert}")
            modified_count += 1
            
            # Add purchase history if none exists
            existing_purchase = Purchase.query.filter_by(product_id=product.id).first()
            if not existing_purchase:
                purchase = Purchase(
                    product_id=product.id,
                    supplier_id=supplier.id,
                    purchase_date=datetime.now() - timedelta(days=random.randint(10, 60)),
                    quantity=random.randint(20, 100),
                    price_per_unit=product.price_in_kshs * 0.8,
                    total_price=product.price_in_kshs * 0.8 * 50
                )
                db.session.add(purchase)
                print(f"Added purchase history for {product.product_name}")
        
        # Set expiration date for some products
        if i % 3 == 0:  # Every third product
            days_until_expiry = random.randint(1, 3)
            product.expiration_date = datetime.now().date() + timedelta(days=days_until_expiry)
            print(f"Set {product.product_name} to expire in {days_until_expiry} days")
            modified_count += 1
    
    db.session.commit()
    print(f"Modified {modified_count} products for testing alerts")

if __name__ == "__main__":
    create_test_data()