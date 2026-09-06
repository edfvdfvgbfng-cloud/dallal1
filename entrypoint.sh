#!/bin/bash

echo "Skipping migrations for now due to database conflicts..."
echo "Starting Django application directly..."
exec python manage.py runserver 0.0.0.0:8000