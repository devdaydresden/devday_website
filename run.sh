#!/bin/bash
# vim: sw=2 ts=2 et si ai

set -e

dbdump=''
mediadump=''
container='app'
DOCKER_COMPOSE="docker-compose -f docker-compose.yml -f docker-compose.dev.yml"
export DOCKER_REGISTRY="${DOCKER_REGISTRY:-devdaydresden}/"  # note trailing /

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
       ./run.sh compose [...]
       ./run.sh coverage
       ./run.sh coveralls
       ./run.sh devdata
       ./run.sh manage [...]
       ./run.sh purge
       ./run.sh -d databasedump.sql.gz -m mediadump.tar.gz restore
       ./run.sh [-c container] shell
       ./run.sh start
       ./run.sh stop
       ./run.sh test
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
    $DOCKER_COMPOSE build $@
    ;;
  compose)
    $DOCKER_COMPOSE $@
    ;;
  coverage)
    if [ -z "$($DOCKER_COMPOSE ps -q)" ]; then
      echo "*** Starting all containers"
      docker_compose_up
    fi
    $DOCKER_COMPOSE exec "${container}" coverage run --branch manage.py test -v1 -k $@
    $DOCKER_COMPOSE exec "${container}" coverage report -m
    $DOCKER_COMPOSE exec "${container}" coverage html
    ;;
  coveralls)
    if [ -z "$($DOCKER_COMPOSE ps -q)" ]; then
      echo "*** Starting all containers"
      docker_compose_up
    fi
    $DOCKER_COMPOSE exec "${container}" env \
      CI_BRANCH="${TRAVIS_BRANCH}" \
      CI_BUILD_URL="${TRAVIS_BUILD_WEB_URL}" \
      CI_NAME="Travis" \
      COVERALLS_REPO_TOKEN="${COVERALLS_REPO_TOKEN}" \
      coveralls
    ;;
  devdata)
    echo "    Starting containers"
    docker_compose_up
    echo "    Compiling translations"
    $DOCKER_COMPOSE exec "${container}" python manage.py compilemessages
    echo "    Running migrations"
    $DOCKER_COMPOSE exec "${container}" python manage.py migrate
    echo "    Filling database"
    $DOCKER_COMPOSE exec "${container}" python manage.py devdata
    ;;
  docker-push)
    if [ -n "$DOCKER_USERNAME" ]; then
      echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
    else
      echo "WARNING: \$DOCKER_USERNAME is not set.  Assuming you're already logged in to Docker" >&2
    fi
    echo "*** Pushing Docker images to Docker hub"
    $DOCKER_COMPOSE push
    ;;
  log|logs)
    $DOCKER_COMPOSE logs -f "${container}"
    ;;
  manage)
    $DOCKER_COMPOSE exec "${container}" python manage.py $@
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
    $DOCKER_COMPOSE exec -T "${container}" tar xz -C /srv/devday/media < "${mediadump}"
    echo "*** Running migrations"
    $DOCKER_COMPOSE exec "${container}" python manage.py migrate
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
    $DOCKER_COMPOSE logs -f "${container}"
    ;;
  stop)
    $DOCKER_COMPOSE down
    ;;
  test)
    if [ -z "$($DOCKER_COMPOSE ps -q)" ]; then
      echo "*** Starting all containers"
      docker_compose_up
    fi
    $DOCKER_COMPOSE exec "${container}" python manage.py test -v1 -k $@
    ;;
  *)
    echo -e "error: unknown action \"${cmd}\":\n" >&2
    usage
    exit 64
    ;;
esac
