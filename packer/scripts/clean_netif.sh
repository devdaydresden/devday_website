#!/bin/sh

set -e

# remove persistent interface naming
rm -f /etc/udev/rules.d/70-persistent-net.rules

# make ifcfg scripts MAC address independent
for ifcfg in $(ls /etc/sysconfig/network-scripts/ifcfg-*)
do
  if [ "$(basename ${ifcfg})" != "ifcfg-lo" ]
  then
    sed -i '/^UUID/d'   $ifcfg
    sed -i '/^HWADDR/d' $ifcfg
  fi
done
