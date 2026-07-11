# Multi-stage build for Nexus Framework
ARG CACHE_BUST=21

# ── Frontend Build Stage ─────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ── Backend Stage ─────────────────────────────────
FROM python:3.11

ARG CACHE_BUST=21
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

# Import the controls library (idempotent)
echo "📚 Importing controls library..."
python manage.py import_controls || echo "⚠️ Controls import skipped"
python manage.py import_erp_fields || echo "⚠️ ERP fields import skipped"

# Create superuser if it doesn't exist
echo "👤 Ensuring superuser..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings.production')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
email = 'eng.murad.ghannam@gmail.com'
password = 'Ghannam2020'
user = User.objects.filter(email__iexact=email).first()
if user is None:
    user = User(email=email, username=email)
user.email = email
user.username = user.username or email
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.set_password(password)
user.save()
print('Superuser ensured:', email)
" || echo "Superuser step skipped"


# Seed demo data (idempotent)
echo "🌱 Seeding demo data..."
python manage.py seed_demo || echo "⚠️ Demo seed skipped"
python manage.py seed_records || echo "⚠️ Records seed skipped"
python manage.py seed_sector_controls || echo "⚠️ Sector controls seed skipped"
python manage.py seed_languages || echo "⚠️ Languages seed skipped"

# Start server with gunicorn
PORT=${PORT:-8000}
echo "🚀 Starting Nexus Framework on port $PORT with gunicorn"
exec gunicorn nexus.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 --worker-tmp-dir /dev/shm --access-logfile - --error-logfile -
EOF

RUN chmod +x /app/start.sh

EXPOSE 8000
CMD ["/app/start.sh"]
