from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Create db instance to be imported by both app and models
db = SQLAlchemy()
migrate = Migrate()