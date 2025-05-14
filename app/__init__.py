from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from app.config import Config
import random
from datetime import datetime


app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

    
db = SQLAlchemy(app)

migrate = Migrate(app, db)


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    product_type = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    product_code = db.Column(db.String(100), unique=True, nullable=True)
    manufacturer = db.Column(db.String(255), nullable=True)
    qr_code = db.Column(db.String(16), unique=True, nullable=False)
    price_in_kshs = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_of_measure = db.Column(db.String(50), nullable=False)
    concentration = db.Column(db.Float, nullable=True)
    storage_temperature = db.Column(db.String(255), nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    hazard_level = db.Column(db.String(255), nullable=True)
    protocol_link = db.Column(db.String(255), nullable=True)
    msds_link = db.Column(db.String(255), nullable=True)
    
    low_stock_alert = db.Column(db.Integer, default=10, nullable=False)
    checkbox_expiry_date = db.Column(db.Boolean, default=False, nullable=True)
    checkbox_hazardous_material = db.Column(db.Boolean, default=False, nullable=True)
    checkbox_controlled_substance = db.Column(db.Boolean, default=False, nullable=True)
    checkbox_requires_regular_calibration = db.Column(db.Boolean, default=False, nullable=True)
    special_instructions = db.Column(db.Text, nullable=True)
    product_images = db.Column(db.LargeBinary, nullable=True)
    date_of_entry = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    


from routes import register_blueprints
register_blueprints(app)