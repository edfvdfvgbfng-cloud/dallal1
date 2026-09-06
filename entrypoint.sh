#!/bin/bash

echo "Running database migrations..."
python manage.py migrate --fake-initial || python manage.py migrate --fake || echo "Migrations may have conflicts, trying to continue..."

echo "Starting Django application..."
exec python manage.py runserver 0.0.0.0:8000