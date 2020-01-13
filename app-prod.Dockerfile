FROM devdaydresden/devday_website_python_base
MAINTAINER Jan Dittberner <jan.dittberner@t-systems.com>
LABEL vendor="T-Systems Multimedia Solutions GmbH"

ARG http_proxy
ARG no_proxy

VOLUME /app/media /app/static /app/logs

WORKDIR /app

RUN apk --no-cache add \
    uwsgi-http \
    uwsgi-python

EXPOSE 7000

COPY docker/app/start-application.sh docker/app/uwsgi.ini docker/app/devday.wsgi /app/
COPY docker/app/vault.crt /usr/local/share/ca-certificates/
COPY devday /app/

RUN update-ca-certificates

ENTRYPOINT ["dumb-init", "/app/start-application.sh"]
