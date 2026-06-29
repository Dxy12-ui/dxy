web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn library_system.wsgi --bind 0.0.0.0:${PORT:-8000}
