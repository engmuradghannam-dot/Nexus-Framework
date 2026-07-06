"""
Nexus Framework - SaaS-Ready Django ERP Settings
Uses django-tenants for true schema-per-tenant isolation.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

_INSECURE_DEFAULT_KEY = 'django-insecure-nexus-dev-key-change-me'
SECRET_KEY = os.getenv('SECRET_KEY', _INSECURE_DEFAULT_KEY)
if not DEBUG and SECRET_KEY == _INSECURE_DEFAULT_KEY:
    raise RuntimeError('SECRET_KEY must be set in production')

_allowed_hosts_env = os.getenv('ALLOWED_HOSTS', '')
if _allowed_hosts_env:
    ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(',') if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    raise RuntimeError('ALLOWED_HOSTS must be set in production')

if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# ========================
# SaaS Configuration
# ========================
SAAS_DEFAULT_TIER = os.getenv('SAAS_DEFAULT_TIER', 'trial')
SAAS_TRIAL_DAYS = int(os.getenv('SAAS_TRIAL_DAYS', '14'))
PLATFORM_DOMAIN = os.getenv('PLATFORM_DOMAIN', 'nexus-erp.com')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Stripe
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# ========================
# django-tenants Configuration
# ========================
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': os.getenv('DB_NAME', 'nexus'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

# Shared apps (available in public schema)
SHARED_APPS = (
    'django_tenants',  # Must be first
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_filters',
    'guardian',
    'django_celery_beat',
    # SaaS apps (shared across all tenants)
    'apps.tenants',
    'apps.billing',
)

# Tenant-specific apps (isolated per schema)
TENANT_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'guardian',
    'rest_framework',
    'rest_framework.authtoken',
    # Nexus ERP modules (tenant-isolated)
    'apps.core',
    'apps.accounts',
    'apps.inventory',
    'apps.buying',
    'apps.selling',
    'apps.manufacturing',
    'apps.hr',
    'apps.crm',
    'apps.projects',
    'apps.assets',
    'apps.workflow',
)

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

# django-tenants models
TENANT_MODEL = "tenants.Tenant"
TENANT_DOMAIN_MODEL = "tenants.Domain"

# ========================
# Middleware
# ========================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django_tenants.middleware.main.TenantMainMiddleware',  # django-tenants tenant resolution
    'apps.core.observability.middleware.ObservabilityMiddleware',  # OpenTelemetry tracing
    'apps.core.observability.middleware.MetricsMiddleware',  # Prometheus metrics
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.CurrentUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ========================
# Auth
# ========================
AUTH_USER_MODEL = 'tenants.TenantUser'  # Global user model
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ========================
# DRF
# ========================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

# ========================
# Redis / Cache
# ========================
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'nexus',
    }
}

# ========================
# Celery
# ========================
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ========================
# Static / Media
# ========================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Tenant-aware storage
DEFAULT_FILE_STORAGE = 'apps.core.storage.TenantStorage'

AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# ========================
# Email
# ========================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
BILLING_FROM_EMAIL = os.getenv('BILLING_FROM_EMAIL', 'billing@nexus-erp.com')

# ========================
# Observability / OpenTelemetry
# ========================
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://tempo:4317')
OTEL_SERVICE_NAME = 'nexus-erp-backend'
OTEL_RESOURCE_ATTRIBUTES = f"service.name={OTEL_SERVICE_NAME},deployment.environment={ENVIRONMENT}"

# ========================
# Plugin System
# ========================
PLUGIN_DIR = os.path.join(BASE_DIR, 'plugins')
PLUGIN_HOT_RELOAD = DEBUG

# ========================
# Logging (Structured for Loki)
# ========================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'apps.core.observability.logging_config.JSONFormatter',
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'filters': {
        'tenant_aware': {
            '()': 'apps.core.observability.logging_config.TenantAwareFilter',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'filters': ['tenant_aware'],
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(BASE_DIR / 'logs' / 'nexus.json'),
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'json',
            'filters': ['tenant_aware'],
        },
    },
    'loggers': {
        'nexus': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'nexus.observability': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}

# ========================
# Internationalization
# ========================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
