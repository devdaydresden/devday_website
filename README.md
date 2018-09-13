# Dev Day website

The Dev Day website is built using [Django CMS](https://www.django-cms.org/).
And consists of a Django CMS content management part and some custom Django
apps for talk, attendee and speaker management.

## Running the development environment

You can run a local development environment easily with Docker and Docker Compose.  Make sure you have a current version both installed.

You can use [rundev.sh](./rundev.sh) to start and stop the Docker containers,
import a database dump, and purge all local data. The necessary Docker images are built on-demand.

## `build`: Build the necessary Docker images

This should only be necessary if Postgres, Django or other service and framework versions change.

```
$ ./rundev.sh build
Building db
Step 1/5 : FROM postgres
 ---> 978b82dc00dc

...

Step 5/5 : COPY httpd.conf /usr/local/apache2/conf/
 ---> Using cache
 ---> bb9f9690b35b
Successfully built bb9f9690b35b
Successfully tagged devday_hp_revproxy:latest
```

## `import`: Start the development environment and import a database dump.

Any preexisting volumes will be deleted first
```
$ ./rundev.sh -d ~/Downloads/devday/db-20180904-133216.sql.gz -m ~/Downloads/devday/media-20180904-133216.tar.gz import
*** Importing database dump /Users/stbe/Downloads/devday/db-20180904-133216.sql.gz and media dump /Users/stbe/Downloads/devday/media-20180904-133216.tar.gz
    Deleting all containers and volumes
Removing network devday_hp_default
WARNING: Network devday_hp_default not found.
Removing volume devday_hp_devday_media
WARNING: Volume devday_hp_devday_media not found.

...

Applying filer.0009_auto_20171220_1635... OK
Applying filer.0010_auto_20180414_2058... OK
*** Import completed
```
## `start`: Run the Django app
Start the development environment. Use existing volumes with data, or if they don't exist, with an empty data set, and run the Django app inside.

```
$ ./rundev.sh start
*** Starting all containers
Creating network "devday_hp_default" with the default driver
Creating devday_hp_db_1 ... done
Creating devday_hp_app_1 ... done
Creating devday_hp_revproxy_1 ... done
*** Running django app
Performing system checks...

System check identified no issues (0 silenced).
September 13, 2018 - 14:50:50
Django version 1.9.8, using settings 'devday.settings.dev'
Starting development server at http://0.0.0.0:8000/
Quit the server with CONTROL-C.
```

## `stop`: Stop the development environment

```
$ ./rundev.sh stop
Stopping devday_hp_revproxy_1 ... done
Stopping devday_hp_app_1      ... done
Stopping devday_hp_db_1       ... done
Removing devday_hp_revproxy_1 ... done
Removing devday_hp_app_1      ... done
Removing devday_hp_db_1       ... done
Removing network devday_hp_default
```

## `purge`: Purge all containers and volumes

```
$ ./rundev.sh purge
*** Purge data
    Deleting all containers and volumes
Stopping devday_hp_revproxy_1 ... done
Stopping devday_hp_app_1      ... done
Stopping devday_hp_db_1       ... done
Removing devday_hp_revproxy_1 ... done
Removing devday_hp_app_1      ... done
Removing devday_hp_db_1       ... done
Removing network devday_hp_default
Removing volume devday_hp_devday_media
Removing volume devday_hp_devday_static
Removing volume devday_hp_pg_data
    Deleting media files
```


# Moving data between systems

The following sections are outdated as of September 2018, and should be deleted once they have been replaced with the current information.

## Creating a data dump

On the production system:

```
sudo -iu devdayprod
mkdir -p dump/devday/fixtures
/srv/devday/devday.sh dumpdata >dump/devday/fixtures/data_dump.json
tar czf content_dump-20171207.tar.gz -C dump devday -C /var/www/html devday
```


## Importing a data dump

On the local laptop:

```
cd .../devday_hp
tar xzf ../content_dump-20171207.tar.gz -C devday
vagrant ssh runbox
cd /vagrant/devday
/srv/devday/devday.sh sqlflush | /srv/devday/devday.sh dbshell   # Daten wegwerfen
/srv/devday/devday.sh loaddata --app devday data_dump
```

# URL Structure of the Dev Day Website

The site has been restructured to allow multiple events to be served concurrently.  Most URLs have been updated, and many of the existing views have been refactored.

## Public Information

* **/** Redirect to current event (as determined by devday/devday/settings/base.py EVENT_ID)
* **/`event`/** Homepage, managed by DjangoCMS
* **/`event`/talk/** List of accepted talks for this event.  Once all accepted talks have been assigned a slot, this will show the session grid.
* **/`event`/talk/*slug*/`ID`** Detail page for an accepted talk, including speaker bio.

## Attendee And Speaker Management

Attendees, including speakers, can review and update their personal information.  People submitting a proposed talk will complete their attendee registration as part of the speaker registration, if they have not registered yet.

* **/account** Attendee account information.

## Speaker And Talk Information

* **/account/speaker** Speaker information; all registered users can input data here, but this is only required if the user wants to submit a talk proposal. The page also lists all talk proposals the user has made, and includes a link to submitting a new talk.  Talks are filtered by the current event (no past talks are shown).

## Committee Members

* **/committee/talks** Overview of all submitted talks, including links to speakers, talks.  The talks pages have the voting and comment functions.
(defined in `devday/talk/url-committee.py`)

## Special URLS

* **/schedule.xml** InfoBeamer data URL.
