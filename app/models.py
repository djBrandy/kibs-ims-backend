from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Product(db.Model):

    __tablename__ = 'products' 

    id = db.Column(db.Integer, primary_key=True)  
    price_in_kshs = db.Column(db.Float, nullable=False)  
    product_name = db.Column(db.String(255), nullable=False)  
    product_type = db.Column(db.String(255), nullable=False)  
    storage_temperature = db.Column(db.String(255), nullable=True)  
    hazard_level = db.Column(db.String(255), nullable=True)  
    protocol_link = db.Column(db.String(255), nullable=True)  
    msds_link = db.Column(db.String(255), nullable=True)  
    low_stock_alert = db.Column(db.Boolean, default=False, nullable=False)  
    product_images = db.Column(db.Text, nullable=True)  
    checkbox_expiry_date = db.Column(db.Boolean, default=False, nullable=False)  
    checkbox_hazardous_material = db.Column(db.Boolean, default=False, nullable=False)  
    checkbox_controlled_substance = db.Column(db.Boolean, default=False, nullable=False)  
    checkbox_requires_regular_calibration = db.Column(db.Boolean, default=False, nullable=False)  
    special_instructions = db.Column(db.Text, nullable=True)  
    category = db.Column(db.String(255), nullable=False)  
    product_code = db.Column(db.String(100), unique=True, nullable=False)  
    manufacturer = db.Column(db.String(255), nullable=False)  
    expiration_date = db.Column(db.Date, nullable=True)  
    storage_location = db.Column(db.String(255), nullable=False)  
    supplier_information = db.Column(db.Text, nullable=False)  
    date_of_entry = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)  

    def __repr__(self):
        return f"<Product {self.product_name}>"
