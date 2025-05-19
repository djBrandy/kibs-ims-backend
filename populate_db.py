from app import create_app, db
from app.models import Product, Category, Order, OrderItem # Import models from models.py
from faker import Faker
import random

app = create_app()
fake = Faker()

with app.app_context():
    # Populate Categories
    categories = []
    for _ in range(5):  # Create 5 categories
        category = Category(name=fake.word().capitalize())
        db.session.add(category)
        categories.append(category)
    db.session.commit()

    # Populate Products
    products = []
    for _ in range(20):  
        product = Product(
            product_name=fake.word().capitalize(),
            product_type=fake.word().capitalize(),
            category=random.choice(categories).name,
            qr_code=fake.uuid4()[:16],
            price_in_kshs=random.uniform(100, 5000),
            quantity=random.randint(10, 100),
            unit_of_measure="units"
        )
        db.session.add(product)
        products.append(product)
    db.session.commit()

    # Populate Orders
    for _ in range(10):  # Create 10 orders
        order = Order(
            customer_name=fake.name(),
            customer_email=fake.email(),
        )
        db.session.add(order)
        db.session.commit()

        # Add Order Items
        for _ in range(random.randint(1, 5)):  # Each order has 1-5 items
            order_item = OrderItem(
                order_id=order.id,
                product_id=random.choice(products).id,
                quantity=random.randint(1, 10),
            )
            db.session.add(order_item)
        db.session.commit()

    print("Database populated with fake data!")