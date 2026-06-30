web: gunicorn library_system.wsgi --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4
release: python manage.py migrate --noinput && python manage.py init_data
