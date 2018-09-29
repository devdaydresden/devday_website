# Dev Day website

The Dev Day website is built using [Django CMS](https://www.django-cms.org/).
The project consists of a Django CMS content management part and some custom Django apps for talk, attendee and speaker management.

## Developing

Information on how to set up a development environment on your machine, running the application, and performing various development and maintaince tasks is detailed in [README.dev.md](README.dev.md). It also includes some application design information.

### Quickstart

To get a local development instance up and running:

1. Install Docker (on macOS and Windows install Docker For Desktop)
1. Install Docker Compose
1. Clone this repository
1. Run `./run.sh devdata` in a shell and wait for it to complete (Windows: use Git Bash)
1. Access the web site at [localhost:8000](http://localhost:8000)
1. Log in as `admin@devday.de` with password `admin`.

## Running A Production Environment

To set up a test or production environment, see [README.prod.md](README.prod.md).

## Contributing

We welcome your ideas and improvements! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

# Credits

This Django project has been made possible by the contributions of:
* Jan Dittberner
* Jeremias Arnstadt
* Felix Herzog
* Stefan Bethke
* Daniel Sy
and the Software Engineering Community at T-Systems Multimedia Solutions GmbH.
