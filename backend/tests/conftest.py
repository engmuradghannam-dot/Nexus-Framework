import pytest
from django.conf import settings

# Ensure settings are configured
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'rest_framework',
            'apps.core',
            'apps.industry',
            'apps.pmo',
            'apps.ai_module',
            'apps.regulatory',
        ],
        DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
    )
