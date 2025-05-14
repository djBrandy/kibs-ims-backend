from flask import Blueprint

from .products import product_bp

blueprints = [product_bp]


def register_blueprints(app):
    for bp in blueprints:
        app.register_blueprint(bp)