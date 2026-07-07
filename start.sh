#!/bin/sh
set -e

cd backend

# Create missing migrations for all apps
python manage.py makemigrations --noinput

# Run migrations
python manage.py migrate --noinput

# Start gunicorn
exec gunicorn nexus.wsgi:application -b 0.0.0.0:${PORT:-8000} --workers 2 --timeout 60
