# Multi-stage build for Nexus Framework
ARG CACHE_BUST=2

# ── Frontend Build Stage ─────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ── Backend Stage ─────────────────────────────────
FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=nexus.settings.production

WORKDIR /app

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
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings.base')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
email = 'eng.murad.ghannam@gmail.com'
password = 'ghannam2020'
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email, email, password)
    print(f'✅ Superuser created: {email}')
else:
    print(f'✅ Superuser already exists: {email}')
" || echo "⚠️ Superuser creation skipped"

# Show database info
echo "📊 Database configuration:"
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings.base')
django.setup()
from django.conf import settings
print(f'   Engine: {settings.DATABASES["default"]["ENGINE"]}')
print(f'   Name: {settings.DATABASES["default"].get("NAME", "N/A")}')
" || true

# Start server
PORT=${PORT:-8000}
echo "🚀 Starting Nexus Framework on port $PORT"
exec python manage.py runserver 0.0.0.0:$PORT
EOF

RUN chmod +x /app/start.sh

EXPOSE 8000
CMD ["/app/start.sh"]
