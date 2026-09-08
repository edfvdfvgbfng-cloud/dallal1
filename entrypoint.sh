#!/bin/bash

echo "=== Starting Django Application on Railway ==="
echo "Environment Variables:"
echo "PORT=${PORT:-8080}"
echo "RAILWAY_PUBLIC_DOMAIN=$RAILWAY_PUBLIC_DOMAIN"
echo "ALLOWED_HOSTS=$ALLOWED_HOSTS"
echo "DEBUG=$DEBUG"
echo "DATABASE_URL exists: $(if [ -n "$DATABASE_URL" ]; then echo "YES"; else echo "NO"; fi)"
echo "SECRET_KEY exists: $(if [ -n "$SECRET_KEY" ]; then echo "YES"; else echo "NO"; fi)"
echo ""

# Check if this is production
if [ "$DEBUG" = "False" ] || [ "$DEBUG" = "false" ] || [ -z "$DEBUG" ]; then
    echo "=== PRODUCTION MODE ==="
    if [ -z "$DATABASE_URL" ]; then
        echo "ERROR: DATABASE_URL is required in production!"
        echo "Set DATABASE_URL in Railway Variables using: \${{Postgres.DATABASE_URL}}"
        exit 1
    fi
    if [ -z "$SECRET_KEY" ]; then
        echo "ERROR: SECRET_KEY is required in production!"
        echo "Set SECRET_KEY in Railway Variables"
        exit 1
    fi
fi

echo "Running Django migrations..."
# Try to drop conflicting index before migrations using Python script
python drop_conflicting_index.py || echo "Could not drop index, trying migrations anyway..."
# Apply migrations normally - DO NOT fake migrations
python manage.py migrate --noinput
if [ $? -ne 0 ]; then
    echo "ERROR: Migrations failed. This is a critical error."
    echo "The database schema may be inconsistent."
    echo "Please check the migration files and database state."
    exit 1
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "Collectstatic failed, continuing..."

echo "Starting Django on port ${PORT:-8080}..."

# Try using gunicorn with Railway's preferred configuration
if command -v gunicorn &> /dev/null; then
    echo "Using gunicorn with optimized configuration for Railway..."
    # Use Railway's recommended worker count: 2 workers, 300s timeout
    exec gunicorn dalal_project.wsgi:application \
        --bind 0.0.0.0:${PORT:-8000} \
        --workers ${GUNICORN_WORKERS:-2} \
        --threads ${GUNICORN_THREADS:-4} \
        --timeout ${GUNICORN_TIMEOUT:-300} \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        --worker-class gthread
else
    echo "Using Django runserver (gunicorn not available)..."
    exec python manage.py runserver 0.0.0.0:${PORT:-8080}
fi