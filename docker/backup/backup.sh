#!/bin/bash

set -ex

cd /app/backup
BACKUPDATE=$(date +%Y%m%d-%H%M%S%z)

pg_dump -U "${DEVDAY_PG_USER}" -h "${DEVDAY_PG_HOST}" -p "${DEVDAY_PG_PORT}" "${DEVDAY_PG_DBNAME}" | gzip > "db-${BACKUPDATE}.sql.gz"
tar czf "media-${BACKUPDATE}.tar.gz" -C /app/media .
