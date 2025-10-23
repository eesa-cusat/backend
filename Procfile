web: gunicorn eesa_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120 --log-file -
release: python manage.py migrate --noinput && python manage.py createcachetable eesa_cache_table --noinput 2>/dev/null || true
