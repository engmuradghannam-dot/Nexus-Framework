"""
Nexus Framework - Production Settings for Railway
"""
from .base import *

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = ['*']

# EXACT domains only
CSRF_TRUSTED_ORIGINS = [
    'https://web-production-38215.up.railway.app',
]

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
