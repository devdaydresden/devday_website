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

To run the Django application for local development you can do the following:

```
vagrant ssh devbox
cd /vagrant
/srv/devday/devday.sh runserver 0.0.0.0:8000
```

You should be able to access the application via http://127.0.0.1:8000/ now.
