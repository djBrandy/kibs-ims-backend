# ims-kibs-backend/routes/__init__.py
from routes.products import product_bp
from routes.audit import audit_bp  # Add this line

def register_blueprints(app):
    app.register_blueprint(product_bp)
    app.register_blueprint(audit_bp)  # Add this line
    # Register other blueprints here as needed
    # app.register_blueprint(other_bp)