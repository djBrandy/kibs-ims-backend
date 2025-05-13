from flask import Blueprint

from .products import product_bp

blueprints = [product_bp]

product_bp = Blueprint('product', __name__)

def register_blueprints(app):
    """Attach all Blueprints to the main Flask app."""
    for bp in blueprints:
        app.register_blueprint(bp)