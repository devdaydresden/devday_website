class profile::postgresql_server(
  $dbhost,
  $dbport,
  $dbname,
  $dbuser,
  $dbpassword,
  $secret = hiera('profile::djangocms::secret'),
  $devday_root = hiera('devday_root', '/srv/devday'),
  $basedir = hiera('profile::wsgi_webserver::basedir', '/vagrant'),
  $dbhostip = hiera('profile::common::dbhostip'),
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

  class { 'postgresql::server':
    listen_addresses => "::1,127.0.0.1,${dbhostip}",
    ipv4acls         => ['host all all 0.0.0.0/0 md5'],
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

  firewalld_service { 'Allow PostgreSQL':
    ensure  => 'present',
    service => 'postgresql',
    zone    => 'public',
  }
}