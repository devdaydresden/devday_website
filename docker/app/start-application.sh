#!/bin/sh

set -e

python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput
uwsgi --ini /app/uwsgi.ini
