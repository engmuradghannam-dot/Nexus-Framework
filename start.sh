#!/bin/sh
set -e

cd backend

# Auto-generate all missing migrations
python manage.py makemigrations core accounts assets buying crm hr inventory manufacturing projects selling workflow --noinput

# Run migrations with fake-initial fallback for first deploy
python manage.py migrate --noinput --fake-initial || python manage.py migrate --noinput

# Start gunicorn
exec gunicorn nexus.wsgi:application -b 0.0.0.0:${PORT:-8000} --workers 2 --timeout 60
