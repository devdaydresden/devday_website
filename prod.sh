#!/bin/sh
# vim: sw=2 ts=2 et

# script to run docker-compose with prod settings

set -e

if [ ! -f prod-env ]; then touch prod-env; fi

VAULT_KEYDIR=docker/vault/config/ssl/private
VAULT_KEY=${VAULT_KEYDIR}/vault.key.pem
VAULT_CERT=docker/vault/config/ssl/vault.crt.pem
DOCKER_COMPOSE="docker-compose -f docker-compose.yml -f docker-compose.prod.yml"

if [ $# -lt 1 ]; then
  cmd=""
else
  cmd="$1"
  shift || true
fi

case "$cmd" in
  backup)
    echo "*** Running backup"
    $DOCKER_COMPOSE -f docker-compose.tools.yml run --rm backup
    ;;
  build)
    # Relevant for production/test environments with full vault setup
    mkdir -p "${VAULT_KEYDIR}"
    if [ ! -f "${VAULT_KEY}" ]; then
      openssl req -new -x509 -config docker/vault/openssl.cnf -out "${VAULT_CERT}"
    elif [ ! -f docker/vault/config/ssl/vault.crt.pem ]; then
      openssl req -new -x509 -config docker/vault/openssl.cnf -key "${VAULT_KEY}" -out "${VAULT_CERT}"
    fi
    openssl x509 -in "${VAULT_CERT}" -out docker/app/vault.crt
    if [ ! -f "prod-env-db" ]; then
      (echo -n "POSTGRES_PASSWORD=" ; dd if=/dev/urandom bs=32 count=1 2>/dev/null | \
        base64 -w 0) > prod-env-db
    fi
    $DOCKER_COMPOSE build $@
    ;;
  manage)
    $DOCKER_COMPOSE exec app python manage.py $@
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
  restart)
    $DOCKER_COMPOSE stop app
    $DOCKER_COMPOSE up --no-deps app
    ;;
  *)
    $DOCKER_COMPOSE $cmd "$@"
    ;;
esac
