web: gunicorn dalal_project.wsgi:application --bind 0.0.0.0 --port $PORT --workers 4 --timeout 120
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput