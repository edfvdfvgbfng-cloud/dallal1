#!/bin/bash

echo "Skipping migrations for now due to database conflicts..."
echo "Starting Django application directly..."

# Use Railway PORT if set, otherwise default to 8000
PORT=${PORT:-8000}

echo "Starting Django on port $PORT..."
echo "Environment variables:"
echo "PORT=$PORT"
echo "RAILWAY_PUBLIC_DOMAIN=$RAILWAY_PUBLIC_DOMAIN"
echo "ALLOWED_HOSTS from env: $ALLOWED_HOSTS"

# Try using gunicorn instead of runserver
if command -v gunicorn &> /dev/null; then
    echo "Using gunicorn..."
    exec gunicorn dalal_project.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
else
    echo "Using Django runserver (gunicorn not available)..."
    exec python manage.py runserver 0.0.0.0:$PORT
fi