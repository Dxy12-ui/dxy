web: gunicorn library_system.wsgi --bind 0.0.0.0:${PORT:-8000}
release: python manage.py migrate --noinput && python manage.py init_data
