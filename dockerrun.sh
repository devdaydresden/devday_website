#!/bin/bash
set -e

if [ -n `docker images -q devday_hp` ]; then
    docker build -t devday_hp .
fi

JOB=$(docker run -d -v `pwd`:/var/www/html -P devday_hp)
docker port $JOB
