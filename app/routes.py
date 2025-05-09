from flask import Blueprint, request, jsonify
from .models import Product, Category, Order, OrderItem
from app import db

bp = Blueprint('main', __name__)

@bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])

@bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([category.to_dict() for category in categories])

@bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    new_order = Order(customer_name=data['customer_name'], customer_email=data['customer_email'])
    db.session.add(new_order)
    db.session.commit()
    return jsonify(new_order.to_dict()), 201

@bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict())