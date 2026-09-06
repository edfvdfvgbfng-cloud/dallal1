#!/bin/bash
# Force Railway to use this script instead of Procfile
echo "Starting Django application..."
python manage.py runserver 0.0.0.0:8000