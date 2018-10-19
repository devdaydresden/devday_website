#!/bin/sh
# vim: sw=2 ts=2 et

# script to run docker-compose with prod settings

set -e

VAULT_DIR=docker/vault
VAULT_SSL=${VAULT_DIR}/config/ssl
VAULT_KEY=${VAULT_SSL}/private/vault.key.pem
VAULT_CERT=${VAULT_SSL}/vault.crt.pem
VAULT_OPENSSL_CNF=${VAULT_DIR}/openssl.cnf

DOCKER_COMPOSE="docker-compose -f docker-compose.yml -f docker-compose.prod.yml"

[ -f "prod-env" ] || touch prod-env
[ -f "prod-env-mail" ] || touch prod-env-mail

if [ $# -lt 1 ]; then
  cmd=""
else
  cmd="$1"
  shift || true
fi

case "$cmd" in
  backup)
    echo "*** Running backup"
    $DOCKER_COMPOSE up -d db
    $DOCKER_COMPOSE exec db sh -c 'while ! pg_isready; do sleep 1; done'
    BACKUPDATA=$(date +%Y%m%d-%H%M%S%z)
    mkdir -p backup
    $DOCKER_COMPOSE exec db pg_dump -U postgres devday | gzip > "backup/prod-db-${BACKUPDATA}.sql.gz"
    $DOCKER_COMPOSE run --rm --no-deps -T --entrypoint "tar cz -C /srv/devday/media ." app > "backup/prod-media-${BACKUPDATA}.tar.gz"
    ;;
  build)
    # Relevant for production/test environments with full vault setup
    mkdir -p "$(dirname "${VAULT_KEY}")"
    [ -f "${VAULT_KEY}" ] || openssl genrsa -out "${VAULT_KEY}" 2048
    [ -f "${VAULT_CERT}" ] || openssl req -new -x509 \
      -config "${VAULT_OPENSSL_CNF}" -key "${VAULT_KEY}" -out "${VAULT_CERT}"
    openssl x509 -in "${VAULT_CERT}" -out docker/app/vault.crt
    if [ -z "$(cat prod-env-mail)" ]; then
cat >prod-env-mail <<EOF
MAILNAME=mail.devday.de
POSTFIX_ROOT_ALIAS=${USER}
POSTFIX_RELAY_HOST=$(hostname -f)
EOF
    fi
    if ! grep -q DEVDAY_ADMINUSER_EMAIL prod-env; then
      echo "DEVDAY_ADMINUSER_EMAIL=admin@devday.de" >> prod-env
    fi
    $DOCKER_COMPOSE build $@
    ;;
  manage)
    $DOCKER_COMPOSE exec app python manage.py $@
    ;;
  restart)
    $DOCKER_COMPOSE stop app
    $DOCKER_COMPOSE up --no-deps app
    ;;
  shell)
    echo "*** Starting shell in 'app' container"
    $DOCKER_COMPOSE exec app bash
    ;;
  startall)
    echo "*** Starting all containers"
    $DOCKER_COMPOSE up -d
    ;;
  start)
    container="${1:-app}"
    $DOCKER_COMPOSE up --no-deps -d "${container}"
    ;;
  stopall)
    $DOCKER_COMPOSE down
    ;;
  stop)
    container="${1:-app}"
    $DOCKER_COMPOSE stop "${container}"
    ;;
  update)
    sh -c "git pull && $DOCKER_COMPOSE up --build -d --no-deps app"
    ;;
  *)
    $DOCKER_COMPOSE $cmd "$@"
    ;;
esac
