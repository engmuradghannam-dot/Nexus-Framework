# Multi-stage build for Nexus Framework
ARG CACHE_BUST=8

# ── Frontend Build Stage ─────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ── Backend Stage ─────────────────────────────────
FROM python:3.11

ARG CACHE_BUST=8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=nexus.settings.production
ENV PORT=8000

WORKDIR /app

# Cache bust to force fresh build
RUN echo "Cache bust: $CACHE_BUST"

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend static files
COPY --from=frontend-build /app/frontend/dist ./staticfiles/

# Create necessary directories
RUN mkdir -p /app/cache /app/media /app/staticfiles

# Create comprehensive startup script
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
set -e

echo "=========================================="
echo "  Nexus Framework - Startup Script"
echo "=========================================="

# Ensure directories exist
mkdir -p /app/cache /app/media /app/staticfiles

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️ Static collection had issues, continuing..."

# Create migrations for new apps
echo "📝 Creating migrations for new apps..."
python manage.py makemigrations hr inventory manufacturing accounts assets buying selling crm --noinput || echo "⚠️ makemigrations had issues, continuing..."

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --noinput || {
    echo "⚠️ Migration failed, trying with fresh SQLite..."
    rm -f /app/db.sqlite3
    python manage.py migrate --noinput
}

# Create superuser if it doesn't exist
echo "👤 Ensuring superuser exists..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings.production')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'eng.murad.ghannam@gmail.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'ghannam2020')
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email, email, password)
    print(f'✅ Superuser created: {email}')
else:
    print(f'✅ Superuser already exists: {email}')
" || echo "⚠️ Superuser creation skipped"


# Start server with gunicorn
PORT=${PORT:-8000}
echo "🚀 Starting Nexus Framework on port $PORT with gunicorn"
exec gunicorn nexus.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 --worker-tmp-dir /dev/shm --access-logfile - --error-logfile -
EOF

RUN chmod +x /app/start.sh

EXPOSE 8000
CMD ["/app/start.sh"]
