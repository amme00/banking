web: gunicorn banking_system.wsgi:application
celery: celery -A banking_system worker -l info
beat: celery -A banking_system beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler