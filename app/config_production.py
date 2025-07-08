import os

class ProductionConfig:
    # Database Configuration (already configured for PythonAnywhere)
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://djbrandy67:Brandon"
        "@djbrandy67.mysql.pythonanywhere-services.com"
        "/djbrandy67$kibs_ims_db"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 60,
        'pool_timeout': 30,
        'pool_size': 5,  # Reduced for PythonAnywhere limits
        'max_overflow': 10,  # Reduced for PythonAnywhere limits
        'connect_args': {'connect_timeout': 10}
    }
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask Configuration - Production Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_flask_secret_change_in_production')
    DEBUG = False  # Always False in production
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 900

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your_jwt_secret_change_in_production')

    # Email Configuration
    SMTP_HOST = 'smtp.yourmail.com'
    SMTP_PORT = 587
    SMTP_USER = 'your@email.com'
    SMTP_PASS = 'your_email_password'

    # AfricasTalking Configuration
    AT_USERNAME = 'your_africastalking_username'
    AT_API_KEY = 'your_africastalking_api_key'

    # Admin Configuration
    ADMIN_ACCESS_CODE = 'your_admin_access_code'

    # API Keys
    COHERE_API_KEY = 'EmP9noMEe5ZoRERoJAxRE3n2onzptiSo1D1D1Dg3'
    UPC_DATABASE_API_KEY = 'E03A35842EE73F796534FF0C15629C9C'

    # Frontend Configuration - Update with your PythonAnywhere domain
    FRONTEND_URL = 'https://djbrandy67.pythonanywhere.com'
    
    # PythonAnywhere specific settings
    PREFERRED_URL_SCHEME = 'https'
    SERVER_NAME = 'djbrandy67.pythonanywhere.com'