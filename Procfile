web: python backend/manage.py migrate && cd backend && gunicorn nexus.wsgi:application --bind 0.0.0.0:$PORT --workers 2
