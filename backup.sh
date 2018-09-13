#!/bin/bash

set -e

docker-compose up -d
docker-compose -f docker-compose.yml -f docker-compose.tools.yml run --rm backup
