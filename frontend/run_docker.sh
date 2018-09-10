#!/bin/bash

set -e

docker run -it --rm -v "$(cd `dirname $0`/..; pwd):/srv/devday" seco/devday_frontend