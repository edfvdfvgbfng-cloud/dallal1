# Production-ready Dockerfile for Dalal Platform
FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    DJANGO_SETTINGS_MODULE=dalal_project.settings \
    USE_WEBSOCKETS=false \
    PYTHONPATH=/app

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

# Copy application files
COPY dalal_project /app/dalal_project/
COPY properties /app/properties/
COPY templates /app/templates/
COPY static /app/static/
COPY manage.py /app/
COPY run_server.py /app/
COPY entrypoint.sh /app/

# Create necessary directories
RUN mkdir -p /app/static /app/staticfiles /app/logs /app/media /app/locale

# Verify Django installation
RUN python -c "import django; print(f'Django {django.__version__} OK')"

# Static files will be collected at runtime by run_server.py
# This avoids database connection issues during build

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]