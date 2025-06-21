#!/usr/bin/env bash

set -o errexit
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

echo "creating superuser"

pyhon manage.py createsuperuser --noinput || true