web: gunicorn eesa_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --max-requests 1000 --max-requests-jitter 50 --timeout 120 --log-file - --access-logfile - --error-logfile -
release: python manage.py migrate --noinput
