from routes.products import product_bp
from routes.supplier import supplier_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.audit import audit_bp
from routes.admin import admin_bp
from routes.alerts import alerts_bp
from routes.analytics import analytics_bp
from routes.metrics import metrics_bp
from routes.role_based_data import role_data_bp
from routes.worker_management import worker_bp
from routes.predictive_restocking import predictive_bp

def register_routes(app):
    app.register_blueprint(product_bp)
    app.register_blueprint(supplier_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(role_data_bp)
    app.register_blueprint(worker_bp)
    app.register_blueprint(predictive_bp)