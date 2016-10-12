#!/bin/sh
#
# Build the virtualenv for production deployment to avoid installing gcc and
# development libraries on production machines
#
# Author: Jan Dittberner <jan.dittberner@t-systems.com>
#
set -ex
cd $(dirname $0)

if [ -d result ]; then
    if [ -f result/devday_hp_venv.tar.gz ]; then
        if [ result/devday_hp_venv.tar.gz -nt ../requirements.txt ]; then
            echo "venv tarball is already fresh"
            exit 0
        fi
    fi
    rm -r result;
fi

mkdir result
docker pull centos:7

cp -a ../requirements.txt .
docker build -t saec/devday_build .
docker run --rm -v $(readlink -f result):/root/result saec/devday_build
