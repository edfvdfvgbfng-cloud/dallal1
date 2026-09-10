#!/bin/bash

# Reduced logging to avoid Railway rate limit
echo "=== Starting Django Application on Railway ==="

# Set DATABASE_URL from Railway PostgreSQL service
if [ -z "$DATABASE_URL" ]; then
    if [ -n "$RAILWAY_POSTGRES_DATABASE_URL" ]; then
        export DATABASE_URL="$RAILWAY_POSTGRES_DATABASE_URL"
    elif [ -n "$POSTGRES_URL" ]; then
        export DATABASE_URL="$POSTGRES_URL"
    fi
fi

# CRITICAL: DATABASE_URL must be set for production
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set"
    exit 1
fi

# Set default environment variables
if [ -z "$DEBUG" ]; then
    export DEBUG="false"
fi

if [ -z "$ALLOWED_HOSTS" ] && [ -n "$RAILWAY_PUBLIC_DOMAIN" ]; then
    export ALLOWED_HOSTS="$RAILWAY_PUBLIC_DOMAIN"
fi

# Generate SECRET_KEY if not set
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
fi

# Merge conflicting migrations if any
python manage.py makemigrations --merge --noinput 2>/dev/null || true

# Fix database state
python manage.py fix_database

# Run migrations
python manage.py migrate --noinput

# Exit if migrations fail
if [ $? -ne 0 ]; then
    echo "ERROR: Migrations failed"
    exit 1
fi

# Create admin user
python create_admin_user.py 2>/dev/null || true

# Collect static files
python manage.py collectstatic --noinput --clear 2>/dev/null || true

# Start application
if command -v gunicorn &> /dev/null; then
    exec gunicorn dalal_project.wsgi:application \
        --bind 0.0.0.0:${PORT:-8000} \
        --workers ${GUNICORN_WORKERS:-2} \
        --threads ${GUNICORN_THREADS:-4} \
        --timeout ${GUNICORN_TIMEOUT:-300} \
        --log-level critical \
        --worker-class gthread
else
    exec python manage.py runserver 0.0.0.0:${PORT:-8080}
fi