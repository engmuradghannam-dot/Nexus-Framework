"""
Nexus Framework - Production Settings for Railway
"""
from .base import *

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Railway-specific hosts - accept all Railway domains
ALLOWED_HOSTS = ['*']

# CSRF - accept ALL origins for Railway (most permissive)
CSRF_TRUSTED_ORIGINS = [
    'https://web-production-38215.up.railway.app',
    'https://*.up.railway.app',
    'https://*.railway.app',
]

# Add dynamic Railway domain if available
_railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
if _railway_domain:
    _full_url = f'https://{_railway_domain}'
    if _full_url not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_full_url)

_railway_static = os.getenv('RAILWAY_STATIC_URL', '')
if _railway_static and _railway_static not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(_railway_static)

CORS_ALLOWED_ORIGINS = [
    'https://web-production-38215.up.railway.app',
    'https://*.up.railway.app',
    'https://*.railway.app',
]

if _railway_domain:
    _full_url = f'https://{_railway_domain}'
    if _full_url not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(_full_url)

# CRITICAL: For cross-origin with credentials, SameSite=None + Secure is required
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # Allow JS to read CSRF cookie
CSRF_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'None'

# Allow CSRF cookie to be sent cross-origin
CSRF_USE_SESSIONS = False

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
