#!/bin/bash

echo "Skipping migrations for now due to database conflicts..."
echo "Starting Django application directly..."

# Use Railway PORT if set, otherwise default to 8000
PORT=${PORT:-8000}

echo "Starting Django on port $PORT..."
exec python manage.py runserver 0.0.0.0:$PORT