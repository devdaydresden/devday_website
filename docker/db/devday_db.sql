#!/bin/sh

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
CREATE USER devday WITH PASSWORD 'devday';
CREATE DATABASE devday ENCODING 'UTF-8' TEMPLATE 'template0';
GRANT CREATE, CONNECT ON DATABASE devday TO devday;
EOSQL
