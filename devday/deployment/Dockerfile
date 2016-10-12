FROM centos:7
MAINTAINER Jan Dittberner <jan.dittberner@t-systems.com>
LABEL vendor=T-Systems\ Multimedia\ Solutions\ GmbH
LABEL devday.release=0.1
RUN yum update -y && yum install -y \
    gcc \
    libjpeg-turbo-devel \
    libpng-devel \
    postgresql-devel \
    python-virtualenv \
    zlib-devel
COPY requirements.txt /root/
VOLUME /root/result
ARG VENV_BASE=/srv/devday
ENV VENV_BASE=${VENV_BASE}
CMD mkdir -p ${VENV_BASE} ; \
    virtualenv ${VENV_BASE}/venv ; \
    . ${VENV_BASE}/venv/bin/activate ; \
    pip install wheel ; \
    pip install -r /root/requirements.txt ; \
    tar czf /root/result/devday_hp_venv.tar.gz -C ${VENV_BASE} venv
