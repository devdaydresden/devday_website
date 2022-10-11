FROM debian:bullseye-slim AS builder
LABEL maintainer="Jan Dittberner <jan.dittberner@t-systems.com>"
LABEL vendor="T-Systems Multimedia Solutions GmbH"

COPY pyproject.toml poetry.lock /python-code/
WORKDIR /python-code/

RUN \
    set -eu ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    export PYTHONBUFFERED=1 ; \
    export PYTHONFAULTHANDLER=1 ; \
    export PIP_NO_CACHE_DIR=off ; \
    export PIP_DISABLE_VERSION_CHECK=on ; \
    export PIP_DEFAULT_TIMEOUT=100 ; \
    apt-get update \
 && apt-get dist-upgrade -y \
 && apt-get install --no-install-recommends -y \
    build-essential \
    ca-certificates \
    curl \
    dumb-init \
    gettext \
    httpie \
    iproute2 \
    libffi-dev \
    libjpeg-dev \
    libjpeg62-turbo \
    libmagic1 \
    libpng-dev \
    libpq-dev \
    libxml2-dev \
    libxslt-dev \
    linux-headers-$(dpkg --print-architecture) \
    openssl \
    procps \
    python3-dev \
    python3-pip \
    zlib1g-dev \
 && python3 -m pip install -U wheel poetry \
 && poetry config virtualenvs.in-project true \ 
 && poetry install \
 && rm -rf /root/.cache /root/.local /tmp/*.json \
 && python3 -m pip uninstall --yes poetry \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

EXPOSE 8000

VOLUME /app
WORKDIR /app

ENTRYPOINT ["dumb-init", "/python-code/.venv/bin/python3", "manage.py", "runserver", "0.0.0.0:8000"]
