"""
Nexus Framework - Django Settings
Enterprise-grade configuration with Redis caching & Celery
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-nexus-dev-key-2026-change-in-production')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = ['*']

# ── SECURITY / CSRF / CORS ───────────────────────
# Get from env or use defaults
_csrf_env = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if _csrf_env:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_env.split(',')]
else:
    CSRF_TRUSTED_ORIGINS = [
        'https://web-production-38215.up.railway.app',
        'https://*.up.railway.app',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]

CORS_ALLOWED_ORIGINS = [
    'https://web-production-38215.up.railway.app',
    'https://*.up.railway.app',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# Cookie settings - conditional on HTTPS
_is_https = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_STATIC_URL')
if _is_https:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    # 'None' requires Secure attribute, use 'Lax' for broader compatibility
    CSRF_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SAMESITE = 'Lax'
else:
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_HTTPONLY = True

# Proxy settings for Railway
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ── APPS ───────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'channels',
]
LOCAL_APPS = [
    'apps.core',
    'apps.pmo',
    'apps.industry',
    'apps.ai_module',
    'apps.regulatory',
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Custom Admin
AUTH_USER_MODEL = 'core.User'

# ── MIDDLEWARE ───────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nexus.urls'
WSGI_APPLICATION = 'nexus.wsgi.application'
ASGI_APPLICATION = 'nexus.asgi.application'

# ── TEMPLATES ────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ── DATABASE ─────────────────────────────────────
# Use DATABASE_URL if provided (Railway/Production), otherwise SQLite
DATABASE_URL = os.getenv('DATABASE_URL', '')

if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    # SQLite fallback - works everywhere without PostgreSQL setup
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ── REDIS / CACHE ────────────────────────────────
REDIS_URL = os.getenv('REDIS_URL', '')

if REDIS_URL:
    try:
        import django_redis
        CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': REDIS_URL,
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                }
            }
        }
        SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
        SESSION_CACHE_ALIAS = 'default'
    except ImportError:
        # django_redis not installed, use file cache
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
                'LOCATION': BASE_DIR / 'cache',
            }
        }
        SESSION_ENGINE = 'django.contrib.sessions.backends.db'
else:
    # No Redis - use file-based cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': BASE_DIR / 'cache',
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ── CHANNELS ─────────────────────────────────────
if REDIS_URL:
    try:
        import channels_redis
        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels_redis.core.RedisChannelLayer',
                'CONFIG': {
                    'hosts': [REDIS_URL],
                },
            },
        }
    except ImportError:
        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels.layers.InMemoryChannelLayer',
            },
        }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# ── CELERY ───────────────────────────────────────
if REDIS_URL:
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
else:
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# ── DRF ──────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# ── SPECTACULAR (OpenAPI) ────────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE': 'Nexus Framework API',
    'DESCRIPTION': 'Enterprise PMO / Industry / AI / Regulatory API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# ── CORS ─────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ── STATIC / MEDIA ───────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── INTERNATIONALIZATION ─────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── SUPERUSER DEFAULT ──────────────────────────────
NEXUS_SUPERUSER_EMAIL = os.getenv('NEXUS_SUPERUSER_EMAIL', 'eng.murad.ghannam@gmail.com')
NEXUS_SUPERUSER_PASSWORD = os.getenv('NEXUS_SUPERUSER_PASSWORD', 'ghannam2020')

# Whitenoise static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
