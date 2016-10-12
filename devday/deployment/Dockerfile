FROM centos:7
MAINTAINER Jan Dittberner <jan.dittberner@t-systems.com>
LABEL vendor=T-Systems\ Multimedia\ Solutions\ GmbH
LABEL devday.release=0.1

ARG VENV_BASE=/srv/devday
ARG HTTP_PROXY=http://proxy:8080/
ARG HTTP_NOPROXY=localhost,127.0.0.1,git.t-systems-mms.eu,.mms-dresden.de,.mms-at-work.de
ENV VENV_BASE ${VENV_BASE}
ENV http_proxy ${HTTP_PROXY}
ENV https_proxy ${HTTP_PROXY}
ENV no_proxy ${HTTP_NOPROXY}

RUN rpm --rebuilddb && \
    yum --setopt=tsflags=nodocs -y update && \
    yum --setopt=tsflags=nodocs -y install \
    gcc \
    libjpeg-turbo-devel \
    libpng-devel \
    postgresql-devel \
    python-virtualenv \
    zlib-devel && \
    rm -rf /var/cache/yum/* && \
    yum clean all

COPY requirements.txt /root/
VOLUME /root/result
CMD mkdir -p ${VENV_BASE} ; \
    virtualenv ${VENV_BASE}/venv ; \
    . ${VENV_BASE}/venv/bin/activate ; \
    pip install wheel ; \
    pip install -r /root/requirements.txt ; \
    tar czf /root/result/devday_hp_venv.tar.gz -C ${VENV_BASE} venv
