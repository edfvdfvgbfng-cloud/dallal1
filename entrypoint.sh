#!/bin/bash

echo "=== Starting Django Application ==="
echo "Environment Variables:"
echo "PORT=${PORT:-8000}"
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
python manage.py migrate --noinput || echo "Migrations failed, continuing..."

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "Collectstatic failed, continuing..."

echo "Starting Django on port ${PORT:-8000}..."

# Try using gunicorn
if command -v gunicorn &> /dev/null; then
    echo "Using gunicorn with 1 worker and 300s timeout..."
    exec gunicorn dalal_project.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 1 --timeout 300 --access-logfile - --error-logfile - --log-level info
else
    echo "Using Django runserver (gunicorn not available)..."
    exec python manage.py runserver 0.0.0.0:${PORT:-8000}
fi