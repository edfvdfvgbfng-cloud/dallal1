# Production-ready Dockerfile for Dalal Platform
# Database Protection: No flush, no reset, only safe migrations
FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    DJANGO_SETTINGS_MODULE=dalal_project.settings \
    USE_WEBSOCKETS=false \
    PYTHONPATH=/app \
    # CRITICAL: Database Protection Settings
    ALLOW_SQLITE_FALLBACK=False \
    DATABASE_PROTECTION_ENABLED=True

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy all application files (filtered by .dockerignore)
COPY . /app/

# Verify directory structure
RUN ls -la /app/ && ls -la /app/dalal_project/

# Create necessary directories and ensure execution permissions
RUN mkdir -p /app/static /app/staticfiles /app/logs /app/media /app/locale && \
    chmod +x /app/entrypoint.sh /app/run_server.py

# Set PYTHONPATH explicitly and verify import
ENV PYTHONPATH=/app
RUN export PYTHONPATH=/app && python -c "import sys; print('Python path:', sys.path); import dalal_project; print('dalal_project import OK')" || \
    (echo "ERROR: dalal_project import failed" && exit 1)

# Verify Django installation
RUN python -c "import django; print(f'Django {django.__version__} OK')"

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
