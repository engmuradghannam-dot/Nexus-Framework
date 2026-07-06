#!/bin/sh
set -e

echo "Waiting for database..."
while ! pg_isready -h db -p 5432 -q -U postgres; do
    sleep 1
done
echo "Database is ready!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting application..."
exec "$@"
