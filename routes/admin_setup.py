from flask import Blueprint, jsonify, request
from app.models import db, User, Admin
from werkzeug.security import generate_password_hash
from flask_migrate import init as migrate_init, migrate, upgrade
import os
import shutil

admin_setup_bp = Blueprint('admin_setup', __name__, url_prefix='/api/admin-setup')

@admin_setup_bp.route('/create-admin', methods=['POST'])
def create_admin_user():
    """Create an admin user in the database"""
    try:
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            return {'message': 'Admin user already exists'}, 400
        
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
        
        return {
            'message': 'Admin user created successfully',
            'username': 'admin',
            'password': 'admin123'
        }, 201
        
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

@admin_setup_bp.route('/db-init', methods=['POST'])
def init_database():
    """Initialize database migrations"""
    try:
        migrate_init()
        return {'message': 'Database migrations initialized'}, 200
    except Exception as e:
        return {'error': str(e)}, 500

@admin_setup_bp.route('/db-migrate', methods=['POST'])
def migrate_database():
    """Create database migration"""
    try:
        data = request.get_json() or {}
        message = data.get('message', 'Migration')
        migrate(message=message)
        return {'message': f'Migration created with message: {message}'}, 200
    except Exception as e:
        return {'error': str(e)}, 500

@admin_setup_bp.route('/db-upgrade', methods=['POST'])
def upgrade_database():
    """Upgrade database to latest migration"""
    try:
        upgrade()
        return {'message': 'Database upgraded'}, 200
    except Exception as e:
        return {'error': str(e)}, 500

@admin_setup_bp.route('/db-reset', methods=['POST'])
def reset_database():
    """Reset database and migrations"""
    try:
        # Drop all tables
        db.drop_all()
        
        # Remove migrations directory
        migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
        if os.path.exists(migrations_dir):
            shutil.rmtree(migrations_dir)
        
        # Initialize migrations
        migrate_init()
        
        return {'message': 'Database reset successfully'}, 200
    except Exception as e:
        return {'error': str(e)}, 500