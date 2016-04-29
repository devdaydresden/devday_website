FROM centos:centos7
ENV http_proxy http://proxy:8080/
ENV https_proxy http://proxy:8080/
ENV no_proxy localhost,127.0.0.1,git.t-systems-mms.eu,.mms-dresden.de,.mms-at-work.de

MAINTAINER Jan Dittberner <jan.dittberner@t-systems.com>

RUN rpm --rebuilddb \
        && yum --setopt=tsflags=nodocs -y update \
        && yum --setopt=tsflags=nodocs -y install \
        httpd \
        php \
        php-cli \
        php-pecl-apc \
        && rm -rf /var/cache/yum/* \
        && yum clean all

RUN sed -i \
        -e '/#<Location \/server-status>/,/#<\/Location>/ s~^#~~' \
        -e '/<Location \/server-status/,/<\/Location>/ s~Allow from .example.com~Allow from localhost 127.0.0.1~' \
        /etc/httpd/conf/httpd.conf

CMD ["/sbin/httpd", "-DFOREGROUND"]

EXPOSE 80
