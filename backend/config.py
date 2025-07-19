import os
from dotenv import load_dotenv

load_dotenv()

def is_production():
    """Check if we're running in production environment"""
    return os.getenv('FLASK_ENV') == 'production' or os.getenv('RENDER') == 'true'

def is_development():
    """Check if we're running in development environment"""
    return not is_production()

class Config:
    # Key/token configuration 
    SECRET_KEY = os.getenv('SECRET_KEY')
    TMDB_API_KEY = os.getenv('TMBD_API_KEY')
    JWT_EXPIRATION_HOURS = 24
    
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', '')
    
    # Environment detection
    IS_PRODUCTION = is_production()
    IS_DEVELOPMENT = is_development()

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    env = os.getenv('FLASK_ENV', 'default')
    return config[env]