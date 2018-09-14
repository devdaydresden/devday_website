#!/bin/bash

set -e

dbdump=''
mediadump=''

OPTIND=1
while getopts 'd:m:h?' opt; do
  case "$opt" in
  h|\?)
    echo "usage: rundev.sh -d databasedump.sql.gz -m mediadump.tar.gz import"
    echo "       rundev.sh manage [...]"
    echo "       rundev.sh purge"
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

cmd="$1"
shift
case "$cmd" in
  backup)
    echo "*** Running backup"
    docker-compose -f docker-compose.yml -f docker-compose.tools.yml run --rm backup
    ;;
  build)
    echo "*** Building Docker images"
    docker-compose build
    ;;
  devdata)
    echo "    Starting containers"
    docker-compose up --detach
    echo "    Running migrations"
    docker-compose exec app python manage.py migrate
    echo "    Filling database"
    docker-compose exec app python manage.py devdata
    ;;
  manage)
    docker-compose exec app python manage.py $@
    ;;
  purge)
    echo "*** Purge data"
    echo "    Deleting all containers and volumes"
    docker-compose down --volumes
    echo "    Deleting media files"
    rm -rf devday/media/*
    ;;
    restore)
      if [ -z "${dbdump}" ]; then
        echo "error: must specify -d databasedump.sql.gz file to restore" >&2
        exit 64
      fi
      if [ -z "${mediadump}" ]; then
        echo "error: must specify -m mediafiles.tar.gz archive to restore" >&2
        exit 64
      fi
      echo "*** Restoring database dump ${dbdump} and media dump ${mediadump}"
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
    echo "error: unknown action \"${cmd}\": specify one of import, manage, purge, start, stop" >&2
    exit 64
    ;;
esac
