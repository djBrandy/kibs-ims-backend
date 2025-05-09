from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Import Flask-Migrate

db = SQLAlchemy()
migrate = Migrate()  # Initialize Flask-Migrate

def create_app():
    app = Flask(__name__)
    
    # MySQL Database Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:#Lerengesu.156@localhost/ims_kibs'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)  # Bind Flask-Migrate to the app and database

    from .routes import bp
    app.register_blueprint(bp)

    return app