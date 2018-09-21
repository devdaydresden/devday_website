FROM node:8-stretch

VOLUME /srv/devday

RUN apt update && \
  apt install -y build-essential ruby ruby-dev && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/* && \
  gem install scss_lint

WORKDIR /srv/devday/frontend

ENV PATH=/srv/devday/frontend/node_modules/.bin:$PATH

CMD /bin/bash
