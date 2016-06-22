# DevDay website

## run local instance in docker

```
./dockerrun.sh
```

> The Dockerfile has not been updated to support Django CMS yet, it can be used
> to serve the static site for DevDay 2016 though

## use Vagrant for local development

The DevDay website is built using [Django CMS](https://www.django-cms.org/).
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
command line.

To re-run the provisioning later (i.e. for changed Puppet manifests) us

```
vagrant provision <boxname>
```

to stop a running virtual machine use

```
vagrant halt <boxname>
```

> All testing has been done using Vagrant 1.8.4 with VirtualBox 5.0.18, if you
> experience issues please update to this versions first.

## build css

CSS is built using [compass](http://compass-style.org/)/[sass](http://sass-lang.com/):

```
compass compile
```
