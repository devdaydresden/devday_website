#!/bin/sh
# vim: sw=2 ts=2 et

set -e

VAULT_API_URL="https://localhost:8200/v1"
CURL="curl --cacert config/ssl/vault.crt.pem"

if [ ! -f "../../prod-env" ]; then
  echo "../../prod-env does not exist. Run ./init_unseal_fill_vault.sh first."
  exit 1
fi

. ../../prod-env

if [ -z "${VAULT_TOKEN}" ]; then
  echo "../../prod-env does not contain a VAULT_TOKEN definition. Run ./init_unseal_fill_vault.sh first."
  exit 1
fi

# try renew
${CURL} --silent --fail -X POST -H "X-Vault-Token: ${VAULT_TOKEN}" --data '{}' ${VAULT_API_URL}/auth/token/renew-self > /dev/null

# print new expiry time
${CURL} --silent -H "X-Vault-Token: ${VAULT_TOKEN}" ${VAULT_API_URL}/auth/token/lookup-self | python -c 'import json, sys; print "Token will expire at", json.load(sys.stdin)["data"]["expire_time"]'

