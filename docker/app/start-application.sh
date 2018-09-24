#!/bin/sh

set -e

python manage.py collectstatic --noinput
python manage.py migrate --noinput
uwsgi --ini /srv/devday/uwsgi.ini
