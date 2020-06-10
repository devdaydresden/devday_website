FROM alpine
MAINTAINER Jan Dittberner <jan.dittberner@t-systems.com>
LABEL vendor="T-Systems Multimedia Solutions GmbH"

ARG http_proxy
ARG https_proxy
ARG no_proxy

ENV \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

RUN apk --no-cache add \
    ca-certificates \
    curl \
    dumb-init \
    gettext \
    git \
    jpeg \
    libmagic \
    libpng \
    libpq \
    libxml2 \
    libxslt \
    openssl \
    python3

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
    apk --no-cache add --virtual build-dependencies \
    build-base \
    gcc \
    jpeg-dev \
    libffi-dev \
    libffi-dev \
    libpng-dev \
    libxml2-dev \
    libxslt-dev \
    linux-headers \
    musl-dev \
    postgresql-dev \
    py3-pip \
    python3-dev \
    zlib-dev \
 && python3 -m pip install -U pip wheel \
 && python3 -m pip install "pipenv <=2018.11.26|>2020.6.2" \
 && pipenv install --three --system --deploy --ignore-pipfile \
 && rm -rf /root/.cache \
 && find / -name __pycache__ -print0|xargs -0 rm -rf \
 && apk del build-dependencies \
 && update-ca-certificates
