# Multi-stage build for Nexus Framework
ARG CACHE_BUST=52

# ── Frontend Build Stage ─────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ── Backend Stage ─────────────────────────────────
FROM python:3.11-slim

ARG CACHE_BUST=52
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=nexus.settings.production
ENV PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

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

# Create startup script - NO hardcoded passwords, NO makemigrations in production
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
python manage.py collectstatic --noinput

# Run migrations ONLY (no makemigrations in production)
echo "🗄️  Running database migrations..."
python manage.py migrate --noinput

# Import the controls library (idempotent)
echo "📚 Importing controls library..."
python manage.py import_controls || echo "⚠️ Controls import skipped"
python manage.py import_erp_fields || echo "⚠️ ERP fields import skipped"

# Create superuser from environment variables ONLY
if [ -n "$NEXUS_SUPERUSER_PASSWORD" ]; then
    echo "👤 Ensuring superuser..."
    python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings.production')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
email = os.environ.get('NEXUS_SUPERUSER_EMAIL')
password = os.environ.get('NEXUS_SUPERUSER_PASSWORD')
if not email or not password:
    print('NEXUS_SUPERUSER_EMAIL / NEXUS_SUPERUSER_PASSWORD not set, skipping superuser bootstrap')
else:
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
else
    echo "⚠️ NEXUS_SUPERUSER_PASSWORD not set, skipping superuser creation"
fi

# Seed demo data (idempotent)
echo "🌱 Seeding demo data..."
python manage.py seed_languages || echo "⚠️ Languages seed skipped"
python manage.py seed_currencies || echo "⚠️ Currencies seed skipped"
python manage.py seed_pricing || echo "⚠️ Pricing seed skipped"
python manage.py seed_uom || echo "⚠️ UOM seed skipped"
python manage.py seed_automation || echo "⚠️ Automation seed skipped"
python manage.py seed_purchasing || echo "⚠️ Purchasing seed skipped"
python manage.py seed_notifications || echo "⚠️ Notifications seed skipped"
python manage.py seed_hr_extras || echo "⚠️ HR extras seed skipped"
python manage.py seed_pmo || echo "⚠️ PMO seed skipped"
python manage.py seed_demo || echo "⚠️ Demo seed skipped"
python manage.py seed_records || echo "⚠️ Records seed skipped"
python manage.py seed_roles || echo "⚠️ Roles seed skipped"
python manage.py seed_attendance || echo "⚠️ Attendance seed skipped"
python manage.py seed_stock || echo "⚠️ Stock seed skipped"
python manage.py seed_trade || echo "⚠️ Trade seed skipped"
python manage.py seed_depreciation || echo "⚠️ Depreciation seed skipped"
python manage.py seed_banking || echo "⚠️ Banking seed skipped"
python manage.py seed_tenants || echo "⚠️ Tenants seed skipped"
python manage.py seed_accounting || echo "⚠️ Accounting seed skipped"
python manage.py seed_invoices || echo "⚠️ Invoices seed skipped"
python manage.py seed_tax_templates || echo "⚠️ Tax templates seed skipped"
python manage.py seed_sector_controls || echo "⚠️ Sector controls seed skipped"

# Start server with gunicorn
PORT=${PORT:-8000}
echo "🚀 Starting Nexus Framework on port $PORT with gunicorn"
exec gunicorn nexus.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 --worker-tmp-dir /dev/shm --access-logfile - --error-logfile -
EOF

RUN chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health/ || exit 1

EXPOSE 8000
CMD ["/app/start.sh"]
