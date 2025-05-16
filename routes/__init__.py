# ims-kibs-backend/routes/__init__.py
from routes.products import product_bp
from routes.audit import audit_bp
from routes.supplier import supplier_bp
from routes.metrics import metrics_bp
from routes.alerts import alerts_bp
from routes.auth import auth_bp
from routes.analytics import analytics_bp

def register_blueprints(app):
    app.register_blueprint(product_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(supplier_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(analytics_bp)
    # Register other blueprints here as needed