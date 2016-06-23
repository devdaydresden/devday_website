class profile::djangocms(
  $dbname,
  $dbuser,
  $dbpassword,
  $dbhost,
  $dbport,
  $secret,
  $devday_root = hiera('devday_root', '/srv/devday'),
  $basedir = hiera('profile::wsgi_webserver::basedir', '/vagrant')
) {
  $django_env = [
    "DJANGO_SETTINGS_MODULE=devday.settings.${::environment}",
    "DEVDAY_PG_DBNAME=${dbname}",
    "DEVDAY_PG_HOST=${dbhost}",
    "DEVDAY_PG_PORT=${dbport}",
    "DEVDAY_PG_USER=${dbuser}",
    "DEVDAY_PG_PASSWORD=${dbpassword}",
    "DEVDAY_SECRET=${secret}",
  ]

  class { 'postgresql::lib::devel':
  }
  package { ['libjpeg-devel', 'zlib-devel', 'gcc', 'libpng-devel']:
    ensure => installed,
  }

  file { $devday_root:
    ensure => directory,
    owner  => 'vagrant',
    group  => 'vagrant',
    mode   => '0755',
  }

  class { 'python':
    version    => 'system',
    pip        => 'present',
    dev        => 'present',
    virtualenv => 'present',
  } ->
  python::virtualenv { "${devday_root}/venv":
    ensure       => present,
    version      => 'system',
    requirements => '/vagrant/devday/requirements.txt',
    owner        => 'vagrant',
    group        => 'vagrant',
    require => [
      Class['postgresql::lib::devel'],
      File[$devday_root],
      Package['gcc'],
      Package['libjpeg-devel'],
      Package['libpng-devel'],
      Package['zlib-devel'],
    ],
  }

  class { 'postgresql::server':
    listen_addresses => '::1,127.0.0.1',
  }

  postgresql::server::db { $dbname:
    user     => $dbuser,
    password => postgresql_password($dbuser, $dbpassword),
  } ->
  exec { "${devday_root}/venv/bin/python manage.py migrate":
    user        => 'vagrant',
    cwd         => "${basedir}/devday",
    environment => $django_env,
  }
}
