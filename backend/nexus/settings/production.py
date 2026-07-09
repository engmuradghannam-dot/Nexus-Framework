"""
Nexus Framework - Production Settings for Railway
"""
from .base import *

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Railway-specific hosts
ALLOWED_HOSTS = [
    'web-production-38215.up.railway.app',
    'localhost',
    '127.0.0.1',
    '*',
]

# CSRF for Railway HTTPS
CSRF_TRUSTED_ORIGINS = [
    'https://web-production-38215.up.railway.app',
    'https://*.up.railway.app',
]

CORS_ALLOWED_ORIGINS = [
    'https://web-production-38215.up.railway.app',
    'https://*.up.railway.app',
]

# Secure cookies
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'None'

# Proxy settings
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
