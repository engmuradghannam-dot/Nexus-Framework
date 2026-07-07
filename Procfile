web: python backend/manage.py migrate && python backend/manage.py collectstatic --noinput && cd backend && gunicorn nexus.wsgi:application --bind 0.0.0.0:$PORT --workers 4
