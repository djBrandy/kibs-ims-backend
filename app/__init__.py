import os
import sys
from flask import Flask, send_from_directory, request, render_template, make_response
# CORS removed - using manual headers
from flask_mail import Mail

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .config import Config
except ImportError:
    from config import Config

try:
    from .database import db, migrate
except ImportError:
    from database import db, migrate



# Initialize extensions
mail = Mail()

# Application Factory


def create_app():
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DIST_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'dist'))

    app = Flask(
        __name__,
        static_folder=DIST_DIR,
        template_folder=DIST_DIR
    )
    app.config.from_object(Config)

    # Initialize extensions with the app context
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    # Disable CORS completely - allow all origins and methods
    @app.after_request
    def after_request(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = '*'
        response.headers['Access-Control-Allow-Headers'] = '*'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Expose-Headers'] = '*'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response
    
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = '*'
            response.headers['Access-Control-Allow-Headers'] = '*'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '86400'
            return response





    # Register blue-printed routes
    from routes import register_routes
    register_routes(app)
    
    # Initialize admin user if it doesn't exist
    with app.app_context():
        try:
            from app.models import User, Admin
            from werkzeug.security import generate_password_hash
            
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    phone='+1234567890',
                    role='admin',
                    is_active=True
                )
                admin.password_hash = generate_password_hash('admin123')
                
                admin_legacy = Admin(
                    username='admin',
                    phone='+1234567890'
                )
                admin_legacy.password_hash = generate_password_hash('admin123')
                
                db.session.add(admin)
                db.session.add(admin_legacy)
                db.session.commit()
        except Exception:
            pass  # Ignore errors during startup

    # Service-worker endpoint (optional)
    @app.route("/service-worker.js")
    def sw():
        sw_path = os.path.join(DIST_DIR, "service-worker.js")
        if os.path.exists(sw_path):
            return send_from_directory(DIST_DIR, "service-worker.js")
        return "", 204

    # Serve vite.svg if available
    @app.route("/vite.svg")
    def vite_svg():
        vite_svg_path = os.path.join(DIST_DIR, "vite.svg")
        if os.path.exists(vite_svg_path):
            return send_from_directory(DIST_DIR, "vite.svg")
        return "", 404

    # Handle favicon requests
    @app.route("/favicon.ico")
    def favicon():
        return "", 204

    # Custom error handler for 404
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    # Catch-all route for frontend requests (assumes a React app)
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        # For API routes that don't exist, return 404
        if path.startswith('api/'):
            return page_not_found(None)

        full_path = os.path.join(DIST_DIR, path)
        if path and os.path.exists(full_path):
            return send_from_directory(DIST_DIR, path)
        return send_from_directory(DIST_DIR, "index.html")

    return app


# Create the singleton application instance
app = create_app()

# Only run the built-in server when executing the file directly.
if __name__ == "__main__":
    # Use PORT from environment variables (Heroku sets this) or default to 5000.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
