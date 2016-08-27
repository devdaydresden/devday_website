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
  $venv = "${devday_root}/venv"

  class { 'postgresql::lib::devel':
  }

  include profile::devpackages

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
  python::virtualenv { $venv:
    ensure       => present,
    version      => 'system',
    requirements => "${basedir}/devday/${::environment}_requirements.txt",
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

  file { "${devday_root}/devday.sh":
    ensure  => file,
    owner   => 'vagrant',
    group   => 'vagrant',
    mode    => '0755',
    content => template('profile/devday/devday.sh.erb'),
    require => File[$devday_root],
  }
}
