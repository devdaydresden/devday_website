#!/bin/sh

docker build --pull $(dirname $0) -t devday-website-frontend
