#!/bin/sh

set -eu

python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput
uwsgi --ini /app/uwsgi.ini
