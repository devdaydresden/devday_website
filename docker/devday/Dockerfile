FROM python:2
MAINTAINER Jan Dittberner <jan.dittberner@t-systems.com>
LABEL vendor=T-Systems\ Multimedia\ Solutions\ GmbH
LABEL devday.release=0.1

ARG HTTP_PROXY=http://proxy.mms-dresden.de:8080/
ARG HTTP_NOPROXY=localhost,127.0.0.1,git.t-systems-mms.eu,.mms-dresden.de,.mms-at-work.de
ARG DEVDAY_POSTGRES_PASSWORD=devday
ARG DEVDAY_SECRET=s3cr3t

ENV http_proxy ${HTTP_PROXY}
ENV https_proxy ${HTTP_PROXY}
ENV no_proxy ${HTTP_NOPROXY}
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE devday.settings.dev
ENV DEVDAY_PG_DBNAME devday
ENV DEVDAY_PG_HOST db
ENV DEVDAY_PG_PORT 5432
ENV DEVDAY_PG_USER devday
ENV DEVDAY_PG_PASSWORD ${DEVDAY_POSTGRES_PASSWORD}
ENV DEVDAY_SECRET ${DEVDAY_SECRET}

EXPOSE 8000
EXPOSE 7000

RUN apt-get update && \
    apt-get install -y uwsgi-plugin-python uwsgi gettext && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    ln -fs /usr/lib/python2.7/plat-x86_64-linux-gnu/_sysconfigdata_nd.py /usr/lib/python2.7/ && \
    mkdir -p /srv/devday

VOLUME /srv/devday/devday /srv/devday/devday/media /srv/devday/devday/static
WORKDIR /srv/devday

ADD devday/dev_requirements.txt devday/requirements.txt /srv/devday/
RUN pip install --upgrade pip && \
    pip install -r dev_requirements.txt

ADD docker/devday/uwsgi.ini /srv/devday/
ADD docker/devday/devday.wsgi /srv/devday/

WORKDIR /srv/devday/devday
CMD ["uwsgi", "--ini", "/srv/devday/uwsgi.ini"]
