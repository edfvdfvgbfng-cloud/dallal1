# Production-ready Dockerfile for Dalal Platform
# Database Protection: No flush, no reset, only safe migrations
# Cache bust: 2026-09-05-04-40
FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    DJANGO_SETTINGS_MODULE=dalal_project.settings \
    USE_WEBSOCKETS=false \
    PYTHONPATH=/app:/app/dalal_project \
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

# Copy all application files
COPY . /app/

# Verify directory structure
RUN ls -la /app/ && \
    echo "Checking dalal_project directory:" && \
    ls -la /app/dalal_project/ && \
    echo "Checking properties directory:" && \
    ls -la /app/properties/

# Create necessary directories and ensure execution permissions
RUN mkdir -p /app/static /app/staticfiles /app/logs /app/media /app/locale && \
    chmod +x /app/entrypoint.sh /app/run_server.py

# Set PYTHONPATH and test import in shell
RUN export PYTHONPATH=/app && \
    python -c "import sys; sys.path.insert(0, '/app'); import dalal_project; print('SUCCESS: dalal_project imported')" || \
    (echo "ERROR: dalal_project import failed. Python path:" && python -c "import sys; print(sys.path)" && exit 1)

# Verify Django installation
RUN python -c "import django; print(f'Django {django.__version__} OK')"

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
