#!/bin/bash

set -e

dbdump=''
mediadump=''

OPTIND=1
while getopts 'd:m:h?' opt; do
  case "$opt" in
  h|\?)
    echo "usage: rundev.sh -d databasedump.sql.gz -m mediadump.tar.gz import"
    echo "       rundev.sh start"
    echo "       rundev.sh stop"
    ;;
  d)
    dbdump="${OPTARG}"
    ;;
  m)
    mediadump="${OPTARG}"
    ;;
  *)
    echo "unknown option \"$opt\"" >&2
    exit 64
    ;;
  esac
done
shift $((OPTIND-1))
[ "${1:-}" = "--" ] && shift

case "$1" in
  build)
    echo "*** Building Docker images"
    docker-compose build
    ;;
  import)
    if [ -z "${dbdump}" ]; then
      echo "error: must specify -d databasedump.sql.gz file to import" >&2
      exit 64
    fi
    if [ -z "${mediadump}" ]; then
      echo "error: must specify -m mediafiles.tar.gz archive to import" >&2
      exit 64
    fi
    echo "*** Importing database dump ${dbdump} and media dump ${mediadump}"
    echo "    Deleting all containers and volumes"
    docker-compose down --volumes
    echo "    Starting containers"
    docker-compose up --detach
    echo "    Waiting for database to be available"
    docker-compose exec db sh -c 'until pg_isready -U devday -d devday; do sleep 1; done'
    echo "    Importing database dump"
    gunzip -c ${dbdump} | docker-compose exec -T db psql -U devday devday
    echo "    Unpacking media dump"
    tar xzf ${mediadump} -C devday
    echo "*** Running migrations"
    docker-compose exec app python manage.py migrate
    echo "*** Import completed"
    ;;
  purge)
    echo "*** Purge data"
    echo "    Deleting all containers and volumes"
    docker-compose down --volumes
    echo "    Deleting media files"
    rm -rf devday/media/*
    ;;
  start|'')
    if [ -z "$(docker-compose ps -q)" ]; then
      echo "*** Starting all containers"
      docker-compose up --detach
    fi
    echo "*** Running django app"
    docker-compose exec app python manage.py runserver 0.0.0.0:8000
    ;;
  stop)
    docker-compose down
    ;;
  *)
    echo "error: unknown action \"$1\": specify one of import, purge, start, stop" >&2
    exit 64
    ;;
esac
