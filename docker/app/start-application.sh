#!/bin/sh

set -e

python3 manage.py compilemessages
python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput
uwsgi --ini /srv/devday/uwsgi.ini
