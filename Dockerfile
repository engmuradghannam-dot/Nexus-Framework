# Multi-stage build for Nexus Framework
ARG CACHE_BUST=1

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
ENV DJANGO_SETTINGS_MODULE=nexus.settings.base

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend static files
COPY --from=frontend-build /app/frontend/dist ./staticfiles/

# Create start script (runs at deploy time when env vars are available)
RUN echo '#!/bin/bash' > start.sh && \
    echo 'set -e' >> start.sh && \
    echo 'echo "Starting Nexus Framework..."' >> start.sh && \
    echo 'python manage.py collectstatic --noinput' >> start.sh && \
    echo 'python manage.py migrate --noinput' >> start.sh && \
    echo 'PORT=${PORT:-8000}' >> start.sh && \
    echo 'echo "Running on port $PORT"' >> start.sh && \
    echo 'python manage.py runserver 0.0.0.0:$PORT' >> start.sh && \
    chmod +x start.sh

EXPOSE 8000
CMD ["./start.sh"]
