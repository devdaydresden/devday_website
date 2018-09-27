#!/bin/bash

set -e

dbdump=''
mediadump=''
container='app'

DOCKER_COMPOSE="docker-compose -f docker-compose.yml -f docker-compose.dev.yml"

docker_compose_up() {
  $DOCKER_COMPOSE up -d
  # fill vault with content
  http_proxy= \
      curl -X POST -H "X-Vault-Token: devday_root" \
      --data '{"data": {"postgresql_password": "devday", "secret_key": "s3cr3t"}}' \
      http://localhost:8200/v1/secret/data/devday
}

usage() {
    cat >&2 <<EOD
usage: ./run.sh backup
       ./run.sh build
       ./run.sh devdata
       ./run.sh manage [...]
       ./run.sh purge
       ./run.sh -d databasedump.sql.gz -m mediadump.tar.gz restore
       ./run.sh [-c container] shell
       ./run.sh start
       ./run.sh stop
EOD
}

OPTIND=1
while getopts 'd:m:c:h?' opt; do
  case "$opt" in
  h|\?)
    usage
    exit
    ;;
  d)
    dbdump="${OPTARG}"
    ;;
  m)
    mediadump="${OPTARG}"
    ;;
  c)
    container="${OPTARG}"
    ;;
  *)
    echo "unknown option \"$opt\"" >&2
    usage
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
    $DOCKER_COMPOSE -f docker-compose.tools.yml run --rm backup
    ;;
  build)
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
  log|logs)
    $DOCKER_COMPOSE logs -f app
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
    docker_compose_up
    echo "    Waiting for database to be available"
    $DOCKER_COMPOSE exec db sh -c 'until pg_isready -U devday -d devday; do sleep 1; done'
    echo "    Importing database dump"
    gunzip -c "${dbdump}" | $DOCKER_COMPOSE exec -T db psql -U devday devday
    echo "    Unpacking media dump"
    $DOCKER_COMPOSE exec -T app tar xz -C /srv/devday/devday/media < "${mediadump}"
    echo "*** Running migrations"
    $DOCKER_COMPOSE exec app python manage.py migrate
    echo "*** Import completed"
    ;;
  shell)
    echo "*** Starting shell in ${container} container"
    $DOCKER_COMPOSE exec "${container}" bash
    ;;
  start|'')
    if [ -z "$($DOCKER_COMPOSE ps -q)" ]; then
      echo "*** Starting all containers"
      docker_compose_up
    fi
    #$DOCKER_COMPOSE exec app python manage.py runserver 0.0.0.0:8000
    $DOCKER_COMPOSE logs -f app
    ;;
  stop)
    $DOCKER_COMPOSE down
    ;;
  *)
    echo -e "error: unknown action \"${cmd}\":\n" >&2
    usage
    exit 64
    ;;
esac
