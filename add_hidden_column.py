from app import db
from flask import Flask
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def add_hidden_column():
    with app.app_context():
        try:
            # Add hidden_from_workers column to products table
            db.engine.execute("ALTER TABLE products ADD COLUMN hidden_from_workers BOOLEAN DEFAULT FALSE")
            print("Added hidden_from_workers column to products table")
            
            # Create pending_deletes table if it doesn't exist
            db.engine.execute("""
            CREATE TABLE IF NOT EXISTS pending_deletes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                worker_id INT,
                product_id INT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending',
                FOREIGN KEY (worker_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
            """)
            print("Created or verified pending_deletes table")
            
            print("Database migration completed successfully")
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            
if __name__ == "__main__":
    add_hidden_column()