#!/bin/sh

set -e

NEW_HOSTNAME=$1

cat <<EOD > /etc/sysconfig/network
NETWORKING=yes
HOSTNAME=$NEW_HOSTNAME
EOD

cat <<EOD > /etc/hosts
127.0.0.1 $NEW_HOSTNAME localhost.localdomain localhost
EOD

/bin/hostname $NEW_HOSTNAME
