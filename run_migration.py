from flask_migrate import upgrade
from app import app, db
from app.models import User
from werkzeug.security import generate_password_hash
import os

def run_migrations():
    with app.app_context():
        # Run migrations
        upgrade()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@kibs-ims.com',
                phone='1234567890',
                role='admin',
                is_active=True
            )
            admin.password_hash = generate_password_hash('admin')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created")

if __name__ == '__main__':
    run_migrations()