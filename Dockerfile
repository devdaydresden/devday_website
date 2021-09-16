FROM debian:buster-slim AS builder

RUN set -eu ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    apt-get update \
 && apt-get install --no-install-recommends --yes \
    build-essential \
    ca-certificates \
    curl \
    dumb-init \
    gettext \
    gettext-base \
    libffi-dev \
    libjpeg-dev \
    libjpeg62-turbo \
    libmagic1 \
    libpng-dev \
    libpng16-16 \
    libpq-dev \
    libpq5 \
    libxml2 \
    libxml2-dev \
    libxslt-dev \
    libxslt1.1 \
    linux-headers-$(dpkg --print-architecture) \
    openssl \
    python3 \
    python3-dev \
    python3-pip \
    uwsgi \
    uwsgi-plugin-python3 \
    zlib1g-dev \
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
    export PIPENV_USE_SYSTEM=1 \
 && python3 -m pip install -U pip wheel pipenv \
 && pipenv install --three --system --deploy --ignore-pipfile \
 && rm -rf /root/.cache /root/.local /tmp/*.json \
 && python3 -m pip uninstall --yes pipenv

COPY devday /app/
RUN set -eu ; \
    cd /app ; \
    echo 'SECRET_KEY="dummy"' > compilemessages_settings.py \
 && DJANGO_SETTINGS_MODULE=compilemessages_settings python3 manage.py compilemessages \
 && rm -rf compilemessages_settings.py __pycache__ /var/lib/apt/lists/*

FROM debian:buster-slim
LABEL maintainer="Jan Dittberner <jan.dittberner@t-systems.com>"
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
    uwsgi \
    uwsgi-plugin-python3 \
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

WORKDIR /app
EXPOSE 7000

COPY devday /app/

COPY docker/app/start-application.sh docker/app/uwsgi.ini docker/app/devday.wsgi /app/

COPY --from=builder /usr/local/lib/python3.7/dist-packages /usr/local/lib/python3.7/dist-packages
COPY --from=builder /app/attendee/locale/de/LC_MESSAGES/django.mo /app/attendee/locale/de/LC_MESSAGES/
COPY --from=builder /app/devday/locale/de/LC_MESSAGES/django.mo /app/devday/locale/de/LC_MESSAGES/
COPY --from=builder /app/event/locale/de/LC_MESSAGES/django.mo /app/event/locale/de/LC_MESSAGES/
COPY --from=builder /app/speaker/locale/de/LC_MESSAGES/django.mo /app/speaker/locale/de/LC_MESSAGES/
COPY --from=builder /app/sponsoring/locale/de/LC_MESSAGES/django.mo /app/sponsoring/locale/de/LC_MESSAGES/
COPY --from=builder /app/talk/locale/de/LC_MESSAGES/django.mo /app/talk/locale/de/LC_MESSAGES/
COPY --from=builder /app/twitterfeed/locale/de/LC_MESSAGES/django.mo /app/twitterfeed/locale/de/LC_MESSAGES/

RUN python3 -m compileall /app
RUN mkdir -p /app/media /app/static /app/logs ; \
    chown -R devday.devday /app/media /app/static /app/logs
VOLUME /app/media /app/static /app/logs
USER devday

ENTRYPOINT ["dumb-init", "/app/start-application.sh"]
