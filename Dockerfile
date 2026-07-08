# Multi-stage build for Nexus Framework
ARG CACHE_BUST=1

# ── Frontend Build Stage ─────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ── Backend Stage ─────────────────────────────────
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend static files
COPY --from=frontend-build /app/frontend/dist ./staticfiles/

# Collect Django static files
RUN python manage.py collectstatic --noinput || true

# Create start script
RUN echo '#!/bin/bash\npython manage.py migrate --noinput\npython manage.py runserver 0.0.0.0:8000' > start.sh && chmod +x start.sh

EXPOSE 8000
CMD ["./start.sh"]
