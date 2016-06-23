# -*- mode: ruby -*-
# vi: set ft=ruby sw=2 ts=2 et:

Vagrant.configure(2) do |config|
  config.vm.box = "centos7-x86_64_virtualbox"
  config.vm.box_url = "http://vagrant-boxes.mms-at-work.de/devday-boxes/centos7-x86_64_virtualbox.json"
  config.vm.box_check_update = true

  # box containing the runtime environment mimicing production
  config.vm.define "runbox" do |runbox|
    runbox.vm.hostname = 'runbox.local'
    runbox.vm.network "forwarded_port", guest: 80, host: 8080
    runbox.vm.network "forwarded_port", guest: 443, host: 8443
    runbox.vm.network "forwarded_port", guest: 5432, host: 15432
    runbox.vm.network "private_network", ip: "192.168.199.200"
  end

  # box containing development tools
  config.vm.define "devbox" do |devbox|
    devbox.vm.hostname = 'devbox.local'
  end

  config.vm.provision "shell", inline: <<-SHELL
    if rpm -q puppet-agent; then
      echo "Puppet agent is already installed"
    else
      wget -q http://yum.puppetlabs.com/RPM-GPG-KEY-puppetlabs http://yum.puppetlabs.com/puppetlabs-release-pc1-el-7.noarch.rpm
      sudo rpm --import RPM-GPG-KEY-puppetlabs
      sudo rpm -K puppetlabs-release-pc1-el-7.noarch.rpm
      sudo rpm -ivh puppetlabs-release-pc1-el-7.noarch.rpm
      sudo yum update
      sudo yum install -y puppet-agent
    fi
    if rpm -q rubygems; then
      echo "Rubygems is already installed"
    else
      sudo yum install -y rubygems
    fi
    if gem list | grep -q librarian-puppet; then
      echo "librarian-puppet is already installed"
    else
      sudo gem install librarian-puppet
    fi
    cd /tmp/vagrant-puppet/environments/dev
    /usr/local/bin/librarian-puppet install --verbose
  SHELL
  config.vm.provision "puppet" do |puppet|
    puppet.environment = "dev"
    puppet.options = ["--verbose"]
    puppet.environment_path = "puppet/environments"
    puppet.hiera_config_path = "puppet/hiera.yaml"
    puppet.working_directory = "/tmp/vagrant-puppet"
  end
end
