#!/bin/sh

set -eu

/python-code/.venv/bin/python3 manage.py migrate --noinput
/python-code/.venv/bin/python3 manage.py collectstatic --noinput
uwsgi --ini /app/uwsgi.ini
