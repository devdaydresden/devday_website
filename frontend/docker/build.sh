#!/bin/sh

docker build --build-arg "http_proxy=${http_proxy}" --build-arg "no_proxy=${no_proxy}" $(dirname $0) -t seco/devday_frontend
