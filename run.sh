#!/bin/bash
# vim: sw=2 ts=2 et si ai

set -e

dbdump=''
mediadump=''
container='app'


setup_postgres_root_password() {
  # define initial PostgreSQL root password
  [ -f "dev-env-db" ] || touch dev-env-db

  grep -q POSTGRES_PASSWORD dev-env-db \
    || echo "POSTGRES_PASSWORD=$(openssl rand -base64 30)" >dev-env-db
}

setup_dev_env() {
  [ -f "dev-env" ] || touch dev-env

  grep -q POSTGRESQL_PASSWORD dev-env \
    || echo 'POSTGRESQL_PASSWORD=devday' >>dev-env
  grep -q SECRET_KEY dev-env \
    || echo "SECRET_KEY=$(openssl rand -base64 30)" >>dev-env
  grep -q CONFIRMATION_SALT dev-env \
    || echo "CONFIRMATION_SALT=$(openssl rand -base64 30)" >>dev-env
  grep -q "ADMINS=" dev-env \
    || echo "ADMINS=Local Admin <admin@devday.de>" >>dev-env
  grep -q "DEBUG=" dev-env \
    || echo "DEBUG=true" >>dev-env
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
       ./run.sh messages
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

touch dev-env

case "$cmd" in
  backup)
    echo "*** Running backup"
    docker compose up -d db
    docker compose exec db sh -c 'while ! pg_isready; do sleep 1; done'
    BACKUPDATA=$(date +%Y%m%d-%H%M%S%z)
    mkdir -p backup
    docker compose exec db pg_dump -U postgres devday | gzip > "backup/dev-db-${BACKUPDATA}.sql.gz"
    docker compose run --rm --no-deps -T --entrypoint "tar cz -C /app/media ." app > "backup/dev-media-${BACKUPDATA}.tar.gz"
    ;;
  build)
    echo "*** Building Docker images"
    setup_postgres_root_password
    setup_dev_env
    docker compose build $@
    ;;
  compose)
    docker compose $@
    ;;
  coverage)
    if [ -z "$(docker compose ps -q)" ]; then
      echo "*** Starting all containers"
      docker compose up -d
    fi
    docker compose exec "${container}" coverage run --branch manage.py test -v1 --keepdb $@
    docker compose exec "${container}" coverage report -m
    docker compose exec "${container}" coverage html
    ;;
  coveralls)
    if [ -z "$(docker compose ps -q)" ]; then
      echo "*** Starting all containers"
      docker_compose up -d
    fi
    docker compose exec "${container}" env \
      CI_BRANCH="${TRAVIS_BRANCH}" \
      CI_BUILD_URL="${TRAVIS_BUILD_WEB_URL}" \
      CI_NAME="Travis" \
      COVERALLS_REPO_TOKEN="${COVERALLS_REPO_TOKEN}" \
      coveralls
    ;;
  devdata)
    echo "    Starting containers"
    setup_postgres_root_password
    setup_dev_env
    docker compose up -d
    echo "    Compiling translations"
    docker compose exec "${container}" python3 manage.py compilemessages
    echo "    Running migrations"
    docker compose exec "${container}" python3 manage.py migrate
    echo "    Filling database"
    docker compose exec "${container}" python3 manage.py devdata
    ;;
  docker-push)
    if [ -n "$DOCKER_USERNAME" ]; then
      echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
    else
      echo "WARNING: \$DOCKER_USERNAME is not set.  Assuming you're already logged in to Docker" >&2
    fi
    echo "*** Pushing Docker images to Docker hub"
    docker compose push
    ;;
  log|logs)
    docker compose logs -f "${container}"
    ;;
  manage)
    docker compose exec "${container}" python3 manage.py $@
    ;;
  messages)
    docker compose exec "${container}" python3 manage.py makemessages -l de --no-obsolete
    docker compose exec "${container}" python3 manage.py compilemessages -l de
    ;;
  purge)
    echo "*** Purge data"
    echo "    Deleting all containers and volumes"
    docker compose down --volumes
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
    docker compose down --volumes
    echo "    Starting containers"
    docker compose up -d
    echo "    Waiting for database to be available"
    docker compose exec db sh -c 'until pg_isready -U devday -d devday; do sleep 1; done'
    echo "    Importing database dump"
    gunzip -c "${dbdump}" | docker compose exec -T db psql -U devday devday
    echo "    Unpacking media dump"
    docker compose exec -T "${container}" tar xz -C /app/media < "${mediadump}"
    echo "*** Running migrations"
    docker compose exec "${container}" python3 manage.py migrate
    echo "*** Import completed"
    ;;
  shell)
    echo "*** Starting shell in ${container} container"
    docker compose exec "${container}" sh
    ;;
  start|'')
    if [ -z "$(docker compose ps -q)" ]; then
      echo "*** Starting all containers"
      setup_postgres_root_password
      setup_dev_env
      docker compose up -d
    fi
    docker compose logs -f "${container}"
    ;;
  stop)
    docker compose down
    ;;
  test)
    if [ -z "$(docker compose ps -q)" ]; then
      echo "*** Starting all containers"
      docker compose up -d
    fi
    docker compose exec "${container}" python3 manage.py test -v1 -k $@
    ;;
  *)
    echo -e "error: unknown action \"${cmd}\":\n" >&2
    usage
    exit 64
    ;;
esac
