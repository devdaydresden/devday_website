#!/usr/bin/env bash

set -e

ARCH=x86_64

case $PACKER_OSVERSION in 
    CentOS5)
        RPMFORGE_VERSION=0.5.3-1.el5.rf
        ;;
    CentOS6)
        RPMFORGE_VERSION=0.5.3-1.el6.rf
        ;;
    *)
        echo "unknown os $PACKER_OSVERSION"
        exit 1
        ;;
esac

wget -q http://apt.sw.be/RPM-GPG-KEY.dag.txt \
        http://pkgs.repoforge.org/rpmforge-release/rpmforge-release-${RPMFORGE_VERSION}.${ARCH}.rpm

rpm --import RPM-GPG-KEY.dag.txt
rpm -K rpmforge-release-${RPMFORGE_VERSION}.${ARCH}.rpm
rpm -ivh rpmforge-release-${RPMFORGE_VERSION}.${ARCH}.rpm

yum install -y --enablerepo=rpmforge-extras git
