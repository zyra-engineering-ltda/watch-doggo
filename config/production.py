import os

class ProductionConfig:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-production-secret-key-here'
    DEBUG = False
    TESTING = False
    
    # Monitoring settings
    CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', 300))  # 5 minutes
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 30))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', '/var/log/leadconduit-monitor/app.log')
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'