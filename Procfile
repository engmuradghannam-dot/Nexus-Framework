web: cd backend && python manage.py migrate && gunicorn nexus.wsgi:application --bind 0.0.0.0:$PORT --workers 4
