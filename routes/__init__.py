# ims-kibs-backend/routes/__init__.py
from routes.products import product_bp
from routes.audit import audit_bp
from routes.supplier import supplier_bp
from routes.metrics import metrics_bp
from routes.alerts import alerts_bp

def register_blueprints(app):
    app.register_blueprint(product_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(supplier_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(alerts_bp)
    # Register other blueprints here as needed