#!/bin/sh
# vim: sw=2 ts=2 et

set -e

# initialize vault
VAULT_API_URL="https://localhost:8200/v1"
VAULT_KEY_FILE="${1:-vault-$(date +%Y%m%d-%H%M%S%z).json}"
CURL="curl --cacert config/ssl/vault.crt.pem"

echo "Unseal keys and root token are kept in ${VAULT_KEY_FILE}"

INIT_STATUS=$(${CURL} --silent ${VAULT_API_URL}/sys/init | \
  python -c 'import json, sys; print json.load(sys.stdin)["initialized"]')

if [ "${INIT_STATUS}" = "True" ]; then
  if [ ! -f "${VAULT_KEY_FILE}" ]; then
    echo "Vault is already initialized, but ${VAULT_KEY_FILE} does not exist."
    echo "Specify an existing key file to continue with the unseal process."
    exit 1
  fi
else
  ${CURL} --silent -X PUT --data '{"secret_shares": 3, "secret_threshold": 2}' \
    ${VAULT_API_URL}/sys/init > "${VAULT_KEY_FILE}"
  echo "Initialization successful."
fi

if ${CURL} --fail --silent ${VAULT_API_URL}/sys/health > /dev/null; then
  echo "Vault is already unsealed"
else
  # unseal vault with 2 of 3 keys
  ${CURL} -X PUT --silent \
    --data "$(printf '{ "key": "%s" }' \
    "$(python -c 'import json, sys; print json.load(sys.stdin)["keys_base64"][0]' < "${VAULT_KEY_FILE}")")" \
    ${VAULT_API_URL}/sys/unseal > /dev/null
  ${CURL} -X PUT --silent \
    --data "$(printf '{ "key": "%s" }' \
    "$(python -c 'import json, sys; print json.load(sys.stdin)["keys_base64"][1]' < "${VAULT_KEY_FILE}")")" \
    ${VAULT_API_URL}/sys/unseal > /dev/null
  ${CURL} --fail --silent ${VAULT_API_URL}/sys/health > /dev/null
  echo "Vault unsealed successfully"
fi

ROOT_TOKEN=$(python -c 'import json, sys; print json.load(sys.stdin)["root_token"]' < "${VAULT_KEY_FILE}")

# enable audit logging
HAS_AUDIT_LOGFILE=$(${CURL} --silent -H "X-Vault-Token: ${ROOT_TOKEN}" ${VAULT_API_URL}/sys/audit | \
  python -c 'import json, sys; print "logfile/" in json.load(sys.stdin)')
if [ "${HAS_AUDIT_LOGFILE}" = "True" ]; then
  echo "Audit logging is already initialized"
else
  ${CURL} -X PUT --silent -H "X-Vault-Token: ${ROOT_TOKEN}" \
    --data '{"type":"file", "options": {"file_path": "/vault/logs/audit.log"}}' \
    ${VAULT_API_URL}/sys/audit/logfile
  echo "Enabled audit logging to /vault/logs/audit.log"
fi

# enable versioning for secret backend
IS_SECRET_V2=$(${CURL} --silent -H "X-Vault-Token: ${ROOT_TOKEN}" ${VAULT_API_URL}/sys/mounts/secret/tune | \
  python -c 'import json, sys; print json.load(sys.stdin)["options"]["version"] == "2"')

if [ "${IS_SECRET_V2}" = "True" ]; then
  echo "Secret backend /secret is already versioned (KV 2)"
else
  # enable versioning for secret backend
  ${CURL} -X POST --silent -H "X-Vault-Token: ${ROOT_TOKEN}" \
    --data '{"options": {"version": "2"}}' \
    ${VAULT_API_URL}/sys/mounts/secret/tune
  echo "Enabled versioning for secret mount"
fi

# setup policy
${CURL} -X PUT --fail --silent -H "X-Vault-Token: ${ROOT_TOKEN}" \
  --data "$(printf '{"policy": "%s"}' \
  "$(sed -e ':a' -e 'N' -e '$!ba' -e 's/\n/\\n/g' -e 's/"/\\"/g' < devday_policy.hcl)")" \
  ${VAULT_API_URL}/sys/policy/devday
echo "Uploaded policy devday"

# setup devday item in Vault if it does not exist
if ${CURL} --silent --fail -H "X-Vault-Token: ${ROOT_TOKEN}" ${VAULT_API_URL}/secret/data/devday >/dev/null; then
  echo "${VAULT_API_URL}/secret/data/devday exists, doing nothing."
else
  ${CURL} --silent --fail -X POST -H "X-Vault-Token: ${ROOT_TOKEN}" \
    --data "$(printf '{"data": {"postgresql_password": "%s", "secret_key": "%s"}}' \
    $(dd if=/dev/urandom bs=32 count=1 2>/dev/null | base64 -w 0) \
    $(dd if=/dev/urandom bs=64 count=1 2>/dev/null | base64 -w 0))" \
    ${VAULT_API_URL}/secret/data/devday >/dev/null
  ${CURL} --silent --fail -H "X-Vault-Token: ${ROOT_TOKEN}" ${VAULT_API_URL}/secret/data/devday | python -m json.tool
fi

if [ -f "../../prod-env" ]; then
  . ../../prod-env
  if [ -n "${VAULT_TOKEN}" ]; then
    TOKEN_INFO=$(${CURL} --silent -X POST -H "X-Vault-Token: ${ROOT_TOKEN}" --data "$(printf '{"token": "%s"}' "${VAULT_TOKEN}")" ${VAULT_API_URL}/auth/token/lookup | python -c 'import json, sys; j=json.load(sys.stdin); print "errors" in j and "invalid" or j["data"]["expire_time"]')
    if [ "${TOKEN_INFO}" = "invalid" ]; then
      echo "Current application token is invalid"
    else
      echo "Current application token is valid until ${TOKEN_INFO}"
      echo "To issue a new token you have to remove VAULT_TOKEN from ../../prod-env"
      exit
    fi
  fi
fi

# create application token
APP_TOKEN=$(${CURL} -X POST --silent -H "X-Vault-Token: ${ROOT_TOKEN}" \
  --data '{"policies": ["devday"], "metadata": {"user": "devday"}, "ttl": "24h", "renewable": true}' \
  ${VAULT_API_URL}/auth/token/create | \
  python -c 'import json, sys; print json.load(sys.stdin)["auth"]["client_token"]')
echo "Created application token"

if [ -f "../../prod-env" ]; then
  ENVDATA=$( (grep -v "VAULT_TOKEN=" ../../prod-env || true ; echo "VAULT_TOKEN=${APP_TOKEN}") | sort)
else
  ENVDATA="VAULT_TOKEN=${APP_TOKEN}"
fi

echo "${ENVDATA}" > ../../prod-env
echo "Updated ../../prod-env"
