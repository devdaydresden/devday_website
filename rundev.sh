#!/bin/bash

set -e

docker-compose up -d
docker-compose exec app python manage.py runserver 0.0.0.0:8000
