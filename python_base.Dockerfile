FROM debian:buster-slim
MAINTAINER Jan Dittberner <jan.dittberner@t-systems.com>
LABEL vendor="T-Systems Multimedia Solutions GmbH"

ENV \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

RUN set -eu ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    apt-get update \
 && apt-get install --no-install-recommends --yes \
    ca-certificates \
    curl \
    dumb-init \
    gettext-base \
    libjpeg62-turbo \
    libmagic1 \
    libpng16-16 \
    libpq5 \
    libxml2 \
    libxslt1.1 \
    openssl \
    python3 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN \
    addgroup --gid 10000 devday \
 && adduser \
      --disabled-password \
      --gecos "Application user" \
      --home /app \
      --ingroup devday \
      --no-create-home \
      --uid 10000 \
      devday

COPY Pipfile Pipfile.lock /python-code/
WORKDIR /python-code/

RUN \
    set -eu ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    export PYTHONBUFFERED=1 ; \
    export PYTHONFAULTHANDLER=1 ; \
    export PIP_NO_CACHE_DIR=off ; \
    export PIP_DISABLE_VERSION_CHECK=on ; \
    export PIP_DEFAULT_TIMEOUT=100 ; \
    export PIPENV_HIDE_EMOJIS=true ; \
    export PIPENV_COLORBLIND=true ; \
    export PIPENV_NOSPIN=true ; \
    export PIPENV_DOTENV_LOCATION=config/.env ; \
    export PIPENV_USE_SYSTEM=1 ; \
    apt-get update \
 && apt-get install --no-install-recommends -y \
    build-essential \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libpq-dev \
    libxml2-dev \
    libxslt-dev \
    linux-headers-$(dpkg --print-architecture) \
    python3-dev \
    python3-pip \
    zlib1g-dev \
 && python3 -m pip install -U pip wheel pipenv \
 && pipenv install --three --system --deploy --ignore-pipfile \
 && rm -rf /root/.cache /root/.local /tmp/*.json \
 && python3 -m pip uninstall --yes pipenv \
 && apt-get autoremove --purge -y \
    build-essential \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libpq-dev \
    libxml2-dev \
    libxslt-dev \
    linux-headers-$(dpkg --print-architecture) \
    python3-dev \
    python3-pip \
    zlib1g-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && find /usr/local -type d -name __pycache__ -print0 | xargs -0 rm -rf
