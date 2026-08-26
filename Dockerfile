# RAILWAY_REMOVE_LOGGING - 2026-08-25-05-45 - Remove temporary logging causing AttributeError
# Removed session_engine logging that was causing errors
# Use different base image and completely different structure
FROM python:3.10-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    DJANGO_SETTINGS_MODULE=dalal_project.settings \
    USE_WEBSOCKETS=false \
    PYTHONPATH=/app \
    FORCE_REBUILD=2026_08_25_05_45

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install django && \
    pip install -r requirements.txt

# Copy application files
COPY dalal_project /app/dalal_project/
COPY properties /app/properties/
COPY templates /app/templates/
COPY static /app/static/
COPY manage.py /app/
COPY run_server.py /app/
COPY entrypoint.sh /app/

# Create directories
RUN mkdir -p /app/static /app/staticfiles /app/logs /app/media /app/locale

# Verify Django
RUN python -c "import django; print(f'Django {django.__version__} OK')"

# Run Django commands (skip migrate at build time since DB will be deleted at runtime)
# makemigrations removed from build time - will run in runtime with real database
RUN python manage.py collectstatic --noinput || true

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]