#!/bin/bash

set -e

dbdump=''
mediadump=''

DOCKER_COMPOSE="docker-compose -f docker-compose.yml -f docker-compose.dev.yml"

docker_compose_up() {
  $DOCKER_COMPOSE up --detach
  # fill vault with content
  http_proxy= \
      curl -X POST -H "X-Vault-Token: devday_root" \
      --data '{"data": {"postgresql_password": "devday", "secret_key": "s3cr3t"}}' \
      http://localhost:8200/v1/secret/data/devday
}

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
shift || true

case "$cmd" in
  backup)
    echo "*** Running backup"
    docker-compose -f docker-compose.yml -f docker-compose.tools.yml run --rm backup
    ;;
  build)
    # Relevant for production/test environments with full vault setup
    #mkdir -p docker/vault/config/ssl/private
    #openssl req -new -x509 -config docker/vault/openssl.cnf  -out docker/vault/config/ssl/vault.crt.pem
    echo "*** Building Docker images"
    $DOCKER_COMPOSE build
    ;;
  devdata)
    echo "    Starting containers"
    docker_compose_up
    echo "    Running migrations"
    $DOCKER_COMPOSE exec app python manage.py migrate
    echo "    Filling database"
    $DOCKER_COMPOSE exec app python manage.py devdata
    ;;
  manage)
    $DOCKER_COMPOSE exec app python manage.py $@
    ;;
  purge)
    echo "*** Purge data"
    echo "    Deleting all containers and volumes"
    $DOCKER_COMPOSE down --volumes
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
    $DOCKER_COMPOSE down --volumes
    echo "    Starting containers"
    $DOCKER_COMPOSE up --detach
    echo "    Waiting for database to be available"
    $DOCKER_COMPOSE exec db sh -c 'until pg_isready -U devday -d devday; do sleep 1; done'
    echo "    Importing database dump"
    gunzip -c ${dbdump} | $DOCKER_COMPOSE exec -T db psql -U devday devday
    echo "    Unpacking media dump"
    tar xzf ${mediadump} -C devday
    echo "*** Running migrations"
    $DOCKER_COMPOSE exec app python manage.py migrate
    echo "*** Import completed"
    ;;
  shell)
    echo "*** Starting shell in app container"
    $DOCKER_COMPOSE exec app bash
    ;;
  start|'')
    if [ -z "$($DOCKER_COMPOSE ps -q)" ]; then
      echo "*** Starting all containers"
      docker_compose_up
    fi
    echo "*** Running django app"
    $DOCKER_COMPOSE exec app python manage.py runserver 0.0.0.0:8000
    ;;
  stop)
    $DOCKER_COMPOSE down
    ;;
  *)
    echo "error: unknown action \"${cmd}\": specify one of import, manage, purge, start, stop" >&2
    exit 64
    ;;
esac
