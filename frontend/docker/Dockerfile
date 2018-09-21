FROM node:8-stretch
MAINTAINER Jan Dittberner <jan.dittberner@t-systems.com>
LABEL vendor=T-Systems\ Multimedia\ Solutions\ GmbH
LABEL devday.release=0.1

VOLUME /srv/devday /srv/devday/frontend/node_modules

ARG http_proxy
ARG no_proxy

ENV http_proxy ${http_proxy}
ENV https_proxy ${http_proxy}
ENV no_proxy ${no_proxy}

WORKDIR /srv/devday/frontend

ENV PATH=/srv/devday/frontend/node_modules/.bin:$PATH

CMD /bin/bash
