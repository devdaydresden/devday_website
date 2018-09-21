#!/bin/bash

set -e

# create empty node_modules to avoid creation of a root owned one by the
# container
mkdir -p node_modules

# run yarn to install packages
docker run -it --rm -v "$(cd `dirname $0`/..; pwd):/srv/devday" -v devdayhp_node_modules:/srv/devday/frontend/node_modules seco/devday_frontend yarn

# run container to start a shell where gulp can be run
docker run -it --rm -v "$(cd `dirname $0`/..; pwd):/srv/devday" -v devdayhp_node_modules:/srv/devday/frontend/node_modules seco/devday_frontend
