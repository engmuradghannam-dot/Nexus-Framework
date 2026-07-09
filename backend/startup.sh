#!/bin/bash
set -e

echo "=========================================="
echo "  Nexus Framework - Startup Script"
echo "=========================================="

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️ Static collection had issues, continuing..."

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --noinput || {
    echo "⚠️ Migration failed, trying with fresh SQLite..."
    rm -f db.sqlite3
    python manage.py migrate --noinput
}

# Create superuser if not exists
echo "👤 Checking superuser..."
python manage.py shell << 'EOF'
import os
from django.contrib.auth import get_user_model
User = get_user_model()
email = os.getenv('NEXUS_SUPERUSER_EMAIL', 'eng.murad.ghannam@gmail.com')
password = os.getenv('NEXUS_SUPERUSER_PASSWORD', 'ghannam2020')
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, password=password, first_name='Admin', last_name='User')
    print(f'✅ Superuser {email} created')
else:
    print(f'✅ Superuser {email} already exists')
EOF

# Start server
echo "🚀 Starting server..."
exec gunicorn nexus.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 2
