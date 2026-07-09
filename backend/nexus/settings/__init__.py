import os

if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_STATIC_URL'):
    from .production import *
else:
    from .base import *
