# DevDay website

The DevDay website is built using [Django CMS](https://www.django-cms.org/).
And consists of a Django CMS content management part and some custom Django
apps for talk, attendee and speaker management.

## use Vagrant for local development

For easy local development and deployment testing a
[Vagrant](https://vagrantup.com/)/[VirtualBox](https://www.virtualbox.org/)
setup is provided that builds two local virtual machines:

* ``devbox`` containing development tools and
* ``runbox`` containing a runtime environment that mimics the production
  environment

Both virtual machines are provisioned using a shell provisioner (for setting up
puppet-agent, ruby and librarian-puppet that installs required Puppet modules)
and [Puppet](https://docs.puppet.com/puppet/) to setup tools, services, users,
files and so on.

To start both boxes use:

```
vagrant up
```

If you want to run only one of the virtual machines add the box name to the
command line. Be aware that devbox requires the PostgreSQL instance running in
runbox if you want to use Django runserver command described below.

To re-run the provisioning later (i.e. for changed Puppet manifests) us

```
vagrant provision <boxname>
```

to stop a running virtual machine use

```
vagrant halt <boxname>
```

> All testing has been done using Vagrant 1.9.2 with VirtualBox 5.1.14, if you
> experience issues please update to this versions first.

## Services provided by runbox

The runbox provides a PostgreSQL database that is exposed at 192.168.199.200:5432 as well as an Apache httpd running the
DevDay application using mod_wsgi as it is done in the production environment. The running DevDay site is available at
[http://127.0.0.1:8080/]() (forwarded from Port 80 inside the VM).

## Running the application in devbox

To run the Django application for local development you can do the following:

```
vagrant ssh devbox
cd /vagrant
/srv/devday/devday.sh runserver 0.0.0.0:8000
```

You should be able to access the application at [http://127.0.0.1:8000/](http://127.0.0.1:8000/) now.

## Running the application locally

You may also run the application from your local machine using the services provided by the runbox. This requires a bit
more work than using the devbox though. You need to set the environment variables like it is done by the
`/srv/devday/devday.sh` script before running the application and adapt the variable values.

```
export DEVDAY_PG_DBNAME="devday"
export DEVDAY_PG_HOST="127.0.0.1"
export DEVDAY_PG_PORT="15432"
export DEVDAY_PG_USER="devday"
export DEVDAY_PG_PASSWORD="secret"
export DEVDAY_SECRET="<random_secret_created_during_provisioning>"
export DJANGO_SETTINGS_MODULE='devday.settings.dev'
```

You will also need a Python 2.7 virtualenv with all the dependencies. Such a virtualenv can be created using
[virtualenv](https://virtualenv.pypa.io/en/stable/) or the Virtual Environment support of an IDE (for example PyCharm).
The requirements are defined  in [devday/requirements.txt]() and can be installed by
[pip](https://pypi.python.org/pypi/pip).

## Building dependency archive in isolation

There is a [Docker](https://docker.io/) based script for building an archive with all the Python dependencies for the
site including all required native code with CentOS 7 dependencies in [devday/deployment](). The deployment process
could be improved by using the result of the build script instead of installing the dependencies directly on the target
machine.

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

# URL Structure of the DevDay Website

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
