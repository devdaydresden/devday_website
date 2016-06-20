#!/usr/bin/env bash

# clean logfiles
find /var/log -type f | while read f; do echo -ne '' > $f; done

# clean temporary files
rm -rf /tmp/*

dd if=/dev/zero of=/junk bs=1M
rm -f /junk

sync
