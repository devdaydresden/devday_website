#!/bin/sh

docker build --pull --build-arg "http_proxy=${http_proxy}" --build-arg "no_proxy=${no_proxy}" $(dirname $0) -t devday-website-frontend
