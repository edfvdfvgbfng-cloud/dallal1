# This file is DISABLED - Using Dockerfile + railway.toml instead
# To use Procfile, change builder in railway.toml to "HEROKU"
web: sh -c 'export PYTHONPATH=/app:$PYTHONPATH && python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn dalal_project.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120'
