#!/bin/bash

echo "=== Starting Django Application on Railway ==="
echo "Environment Variables:"
echo "PORT=${PORT:-8080}"
echo "RAILWAY_PUBLIC_DOMAIN=$RAILWAY_PUBLIC_DOMAIN"
echo "ALLOWED_HOSTS=$ALLOWED_HOSTS"
echo "DEBUG=$DEBUG"
echo "DATABASE_URL exists: $(if [ -n "$DATABASE_URL" ]; then echo "YES"; else echo "NO"; fi)"
echo "SECRET_KEY exists: $(if [ -n "$SECRET_KEY" ]; then echo "YES"; else echo "NO"; fi)"
echo "ALLOW_SQLITE_FALLBACK=$ALLOW_SQLITE_FALLBACK"
echo ""

# Set default environment variables if not set (Railway.toml may not work properly)
# Force development mode when using SQLite
if [ -z "$DATABASE_URL" ]; then
    export DEBUG="true"
    echo "Auto-setting DEBUG=true for development mode (no DATABASE_URL)"
elif [ -z "$DEBUG" ] || [ "$DEBUG" = "False" ] || [ "$DEBUG" = "false" ]; then
    export DEBUG="true"
    echo "Auto-setting DEBUG=true for development mode"
fi

if [ -z "$ALLOW_SQLITE_FALLBACK" ]; then
    export ALLOW_SQLITE_FALLBACK="true"
    echo "Auto-setting ALLOW_SQLITE_FALLBACK=true for SQLite fallback"
fi

# Set ALLOWED_HOSTS if not set (use Railway domain)
if [ -z "$ALLOWED_HOSTS" ] && [ -n "$RAILWAY_PUBLIC_DOMAIN" ]; then
    export ALLOWED_HOSTS="$RAILWAY_PUBLIC_DOMAIN"
    echo "Auto-setting ALLOWED_HOSTS to: $ALLOWED_HOSTS"
fi

# Check if this is production mode
if [ "$DEBUG" = "False" ] || [ "$DEBUG" = "false" ]; then
    echo "=== PRODUCTION MODE ==="
    if [ -z "$DATABASE_URL" ]; then
        echo "WARNING: DATABASE_URL is not set. Using SQLite fallback."
        echo "Please set DATABASE_URL in Railway Variables using: \${{Postgres.DATABASE_URL}}"
    fi
    if [ -z "$SECRET_KEY" ]; then
        echo "WARNING: SECRET_KEY is not set. Auto-generating a temporary key."
        echo "Please set SECRET_KEY in Railway Variables for production security."
        # Generate a temporary secret key
        export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
        echo "Generated temporary SECRET_KEY: ${SECRET_KEY:0:20}..."
    fi
else
    echo "=== DEVELOPMENT MODE ==="
    if [ -z "$DATABASE_URL" ]; then
        echo "Using SQLite for development (ALLOW_SQLITE_FALLBACK=true)"
    fi
    if [ -z "$SECRET_KEY" ]; then
        echo "Auto-generating SECRET_KEY for development..."
        export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
        echo "Generated SECRET_KEY: ${SECRET_KEY:0:20}..."
    fi
fi

echo "Running Django migrations..."
# Try to drop conflicting index before migrations using Python script
python drop_conflicting_index.py || echo "Could not drop index, trying migrations anyway..."

# Try to merge conflicting migrations automatically (ignore errors if no conflicts)
echo "Attempting to merge conflicting migrations if any..."
python manage.py makemigrations --merge --noinput 2>/dev/null || echo "No merge needed"

# Create missing migrations for new models (like ActivityLog)
echo "Creating any missing migrations..."
python manage.py makemigrations --noinput 2>/dev/null || echo "No new migrations needed"

# Apply all migrations normally - don't fake any migrations
echo "Applying all migrations..."
python manage.py migrate --noinput
if [ $? -ne 0 ]; then
    echo "ERROR: Migrations failed. This is a critical error."
    echo "The database schema may be inconsistent."
    echo "Please check the migration files and database state."
    exit 1
fi

# Create admin user if it doesn't exist
echo "Creating admin user if needed..."
python create_admin_user.py || echo "Admin user creation failed or already exists"

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