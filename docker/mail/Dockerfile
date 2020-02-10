FROM alpine:latest

ARG http_proxy
ARG no_proxy
RUN http_proxy=${http_proxy} https_proxy=${http_proxy} \
    no_proxy=${no_proxy} \
    apk add --no-cache \
    bash \
    ca-certificates \
    cyrus-sasl-plain \
    cyrus-sasl-login \
    mailx \
    postfix \
    rsyslog \
    runit

COPY service /etc/service
COPY runit_bootstrap /usr/sbin/runit_bootstrap
COPY rsyslog.conf /etc/rsyslog.conf

EXPOSE 25

STOPSIGNAL SIGKILL

ENTRYPOINT ["/usr/sbin/runit_bootstrap"]
