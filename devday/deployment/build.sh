#!/bin/sh
#
# Build the virtualenv for production deployment to avoid installing gcc and
# development libraries on production machines
#
# Author: Jan Dittberner <jan.dittberner@t-systems.com>
#
set -ex
cd $(dirname $0)
docker pull centos:7
docker build -t saec/devday_build .
if [ -d result ]; then
    rm -r result;
fi
mkdir result
docker run --rm -v $(readlink -f result):/root/result saec/devday_build
