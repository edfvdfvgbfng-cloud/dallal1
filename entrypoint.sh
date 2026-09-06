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

exec python manage.py runserver 0.0.0.0:$PORT