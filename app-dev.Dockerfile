FROM devdaydresden/devday_website_python_base
MAINTAINER Jan Dittberner <jan.dittberner@t-systems.com>
LABEL vendor="T-Systems Multimedia Solutions GmbH"

ARG http_proxy
ARG https_proxy
ARG no_proxy

RUN apk --no-cache add \
    ca-certificates \
    dumb-init \
    gettext \
    jpeg \
    libmagic \
    libpng \
    libpq \
    libxml2 \
    libxslt \
    python3

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
    zlib-dev

RUN \
    pipenv install --system --deploy --ignore-pipfile --dev --verbose \
 && rm -rf /root/.cache \
 && find / -name __pycache__ -print0|xargs -0 rm -rf

EXPOSE 8000

VOLUME /app
WORKDIR /app

ENTRYPOINT ["dumb-init", "python3", "manage.py", "runserver", "0.0.0.0:8000"]
