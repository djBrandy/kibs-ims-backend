class Config:
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://djbrandy67:Brandon"
        "@djbrandy67.mysql.pythonanywhere-services.com"
        "/djbrandy67$kibs_ims_db"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 60,
        'pool_timeout': 30,
        'pool_size': 10,
        'max_overflow': 20,
        'connect_args': {'connect_timeout': 10}
    }
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask Configuration
    SECRET_KEY = 'kibs-ims-secret-key-2025'
    DEBUG = False
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 900

    # JWT Configuration
    JWT_SECRET_KEY = 'kibs-jwt-secret-2025'

    # API Keys
    COHERE_API_KEY = 'EmP9noMEe5ZoRERoJAxRE3n2onzptiSo1D1D1Dg3'
    UPC_DATABASE_API_KEY = 'E03A35842EE73F796534FF0C15629C9C'

    # Frontend Configuration
    FRONTEND_URL = 'https://djbrandy67.pythonanywhere.com'