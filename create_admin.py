from app import db
from app.models import User, Admin
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Create an admin user in the database"""
    
    # Check if admin user already exists
    admin_user = User.query.filter_by(username='admin').first()
    if admin_user:
        print("Admin user already exists")
        return
    
    # Create admin in User table
    admin = User(
        username='admin',
        email='admin@example.com',
        phone='+1234567890',
        role='admin',
        is_active=True
    )
    admin.password_hash = generate_password_hash('admin123')
    
    # Also create in Admin table for backward compatibility
    admin_legacy = Admin(
        username='admin',
        phone='+1234567890'
    )
    admin_legacy.password_hash = generate_password_hash('admin123')
    
    # Add to database
    db.session.add(admin)
    db.session.add(admin_legacy)
    db.session.commit()
    
    print("Admin user created successfully")
    print("Username: admin")
    print("Password: admin123")

if __name__ == "__main__":
    create_admin_user()