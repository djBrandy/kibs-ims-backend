from app import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=True)  # For future user authentication
    action_type = db.Column(db.String(50), nullable=False)  # 'quantity_update', 'concentration_update', etc.
    previous_value = db.Column(db.String(255), nullable=True)
    new_value = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship with product
    product = db.relationship('Product', backref='audit_logs', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.product_name if self.product else None,
            'action_type': self.action_type,
            'previous_value': self.previous_value,
            'new_value': self.new_value,
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class InventoryAnalytics(db.Model):
    __tablename__ = 'inventory_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    last_movement_date = db.Column(db.DateTime, nullable=True)
    days_without_movement = db.Column(db.Integer, nullable=True)
    stockout_count = db.Column(db.Integer, default=0)
    last_stockout_date = db.Column(db.DateTime, nullable=True)
    is_dead_stock = db.Column(db.Boolean, default=False)
    is_slow_moving = db.Column(db.Boolean, default=False)
    is_top_product = db.Column(db.Boolean, default=False)
    movement_rank = db.Column(db.Integer, nullable=True)  # Lower is faster moving
    revenue_rank = db.Column(db.Integer, nullable=True)   # Lower is higher revenue
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with product
    product = db.relationship('Product', backref='analytics', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.product_name if self.product else None,
            'last_movement_date': self.last_movement_date.isoformat() if self.last_movement_date else None,
            'days_without_movement': self.days_without_movement,
            'stockout_count': self.stockout_count,
            'last_stockout_date': self.last_stockout_date.isoformat() if self.last_stockout_date else None,
            'is_dead_stock': self.is_dead_stock,
            'is_slow_moving': self.is_slow_moving,
            'is_top_product': self.is_top_product,
            'movement_rank': self.movement_rank,
            'revenue_rank': self.revenue_rank,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }