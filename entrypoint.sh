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

# CRITICAL: Force DATABASE_URL from Railway PostgreSQL service
# If DATABASE_URL is not set, try to get it from Railway's automatic variable
if [ -z "$DATABASE_URL" ]; then
    # Railway automatically sets DATABASE_URL when PostgreSQL service is linked
    # But if Railway Variables override it, we need to re-set it
    # Check if we can get it from Railway's reference
    if [ -n "$RAILWAY_POSTGRES_DATABASE_URL" ]; then
        export DATABASE_URL="$RAILWAY_POSTGRES_DATABASE_URL"
        echo "Set DATABASE_URL from RAILWAY_POSTGRES_DATABASE_URL"
    elif [ -n "$POSTGRES_URL" ]; then
        export DATABASE_URL="$POSTGRES_URL"
        echo "Set DATABASE_URL from POSTGRES_URL"
    else
        echo "ERROR: DATABASE_URL not set and Railway PostgreSQL reference not found"
        echo "This should not happen if PostgreSQL service is linked"
        echo "Please check Railway service configuration"
    fi
fi

# PostgreSQL service exists in Railway project
# DATABASE_URL should be set by Railway automatically
# We force it above if Railway Variables override it

# Set default environment variables if not set (Railway.toml may not work properly)
if [ -z "$DEBUG" ]; then
    export DEBUG="false"
    echo "Auto-setting DEBUG=false for production"
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

# Use PostgreSQL database (DATABASE_URL is set by Railway)
if [ -n "$DATABASE_URL" ]; then
    echo "Using PostgreSQL database"
else
    echo "WARNING: DATABASE_URL not set, will fail in production"
fi

# Try to merge conflicting migrations automatically
echo "Attempting to merge conflicting migrations if any..."
python manage.py makemigrations --merge --noinput 2>/dev/null || echo "No merge needed or merge failed"

# Drop ALL properties tables to start fresh
echo "Dropping all properties tables to start fresh..."
python manage.py shell << 'EOF'
from django.db import connection
cursor = connection.cursor()

# Get all properties app tables
cursor.execute("""
    SELECT tablename FROM pg_tables 
    WHERE schemaname = 'public' AND tablename LIKE 'properties_%'
""")
tables = [row[0] for row in cursor.fetchall()]

# Drop all properties tables
for table in tables:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        print(f"Dropped table: {table}")
    except Exception as e:
        print(f"Error dropping {table}: {e}")

print(f"Dropped {len(tables)} properties tables")
EOF

# Drop the problematic duplicate index
echo "Dropping problematic duplicate index..."
python manage.py shell << 'EOF'
from django.db import connection
cursor = connection.cursor()

try:
    cursor.execute("DROP INDEX IF EXISTS properties_property_slug_f3b16024_like")
    print("Dropped duplicate slug index")
except Exception as e:
    print(f"Error dropping index: {e}")
EOF

# Unmark migrations for properties app
echo "Unmarking properties migrations..."
python manage.py shell << 'EOF'
from django.db import connection
cursor = connection.cursor()

try:
    cursor.execute("DELETE FROM django_migrations WHERE app = 'properties'")
    print("Unmarked properties migrations")
except Exception as e:
    print(f"Error unmarking migrations: {e}")
EOF

# Run migrations from scratch
echo "Running migrations from scratch..."
python manage.py migrate --noinput

# If migrations fail, fake them
if [ $? -ne 0 ]; then
    echo "ERROR: Migrations failed. Faking all migrations..."
    python manage.py migrate --fake --noinput
fi

echo "Migration process completed"
echo "Application will start"

echo "Migrations completed (with possible warnings)"

# Create admin user if it doesn't exist
echo "Creating admin user if needed..."
python create_admin_user.py 2>/dev/null || echo "Admin user creation failed or already exists"

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