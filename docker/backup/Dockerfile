FROM postgres:10
MAINTAINER Jan Dittberner <jan.dittberner@t-systems.com>
LABEL vendor=T-Systems\ Multimedia\ Solutions\ GmbH
LABEL devday.release=0.1

ARG HTTP_PROXY=http://proxy.mms-dresden.de:8080/
ARG HTTP_NOPROXY=localhost,127.0.0.1,git.t-systems-mms.eu,.mms-dresden.de,.mms-at-work.de
ARG DEVDAY_POSTGRES_PASSWORD=devday

ENV http_proxy ${HTTP_PROXY}
ENV https_proxy ${HTTP_PROXY}
ENV no_proxy ${HTTP_NOPROXY}
ENV DEVDAY_PG_DBNAME devday
ENV DEVDAY_PG_HOST db
ENV DEVDAY_PG_PORT 5432
ENV DEVDAY_PG_USER devday
ENV DEVDAY_PG_PASSWORD ${DEVDAY_POSTGRES_PASSWORD}

RUN mkdir -p /app/{backup,media}

VOLUME /app/backup /app/media

ADD backup.sh /app/
WORKDIR /app/backup
ENTRYPOINT /app/backup.sh
