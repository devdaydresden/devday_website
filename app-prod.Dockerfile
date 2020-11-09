FROM devdaydresden/devday_website_python_base
MAINTAINER Jan Dittberner <jan.dittberner@t-systems.com>
LABEL vendor="T-Systems Multimedia Solutions GmbH"

VOLUME /app/media /app/static /app/logs

WORKDIR /app

RUN set -eu ; \
    export DEBIAN_FRONTENT=noninteractive ; \
    apt-get update \
 && apt-get install --no-install-recommends --yes \
    uwsgi \
    uwsgi-plugin-python3 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

EXPOSE 7000

COPY docker/app/start-application.sh docker/app/uwsgi.ini docker/app/devday.wsgi /app/
COPY docker/app/vault.crt /usr/local/share/ca-certificates/
COPY devday /app/

RUN update-ca-certificates

ENTRYPOINT ["dumb-init", "/app/start-application.sh"]
