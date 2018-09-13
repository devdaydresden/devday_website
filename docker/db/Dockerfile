FROM postgres:10
MAINTAINER Jan Dittberner <jan.dittberner@t-systems.com>
LABEL vendor=T-Systems\ Multimedia\ Solutions\ GmbH
LABEL devday.release=0.1

ADD devday_db.sql /docker-entrypoint-initdb.d/init-user-db.sh
