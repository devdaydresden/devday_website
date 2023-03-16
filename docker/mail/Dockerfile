FROM alpine:latest

RUN apk add --no-cache \
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
