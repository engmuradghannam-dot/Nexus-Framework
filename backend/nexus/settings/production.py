"""
Nexus Framework - Production Settings for Railway
"""
from .base import *

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = ['*']

# COMPREHENSIVE CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    'https://web-production-38215.up.railway.app',
    'http://web-production-38215.up.railway.app',
    'https://*.up.railway.app',
    'https://*.railway.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# Add dynamic Railway domains
_railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
if _railway_domain:
    _full_url = f'https://{_railway_domain}'
    if _full_url not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_full_url)

_railway_static = os.getenv('RAILWAY_STATIC_URL', '')
if _railway_static and _railway_static not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(_railway_static)

# Also read from env variable
_csrf_env = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if _csrf_env:
    for o in [o.strip() for o in _csrf_env.split(',')]:
        if o and o not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(o)

CORS_ALLOWED_ORIGINS = [
    'https://web-production-38215.up.railway.app',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

if _railway_domain:
    _full_url = f'https://{_railway_domain}'
    if _full_url not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(_full_url)

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'None'
CSRF_USE_SESSIONS = False

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

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
