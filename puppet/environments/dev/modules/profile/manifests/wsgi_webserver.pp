class profile::wsgi_webserver(
  $user,
  $group,
  $basedir,
  $devday_root = hiera('devday_root', '/srv/devday'),
  $vhost = $::fqdn,
) {
  class { 'apache':
    default_vhost   => false,
    default_mods    => false,
    purge_configs   => true,
    service_restart => '/usr/sbin/apachectl graceful',
    trace_enable    => 'Off',
  }
  include apache::mod::alias
  include apache::mod::deflate
  include apache::mod::rewrite
  include apache::mod::wsgi

  $python = regsubst( $::python_version, '(\d)\.(\d).+', 'python\1.\2')
  $python_path = "${devday_root}/venv/lib/${python}/site-packages/"
  $devday_dbname = hiera('profile::djangocms::dbname', 'devday')
  $devday_dbuser = hiera('profile::djangocms::dbuser', 'devday')
  $devday_dbhost = hiera('profile::djangocms::dbhost', 'localhost')
  $devday_dbport = hiera('profile::djangocms::dbport', '5432')
  $devday_dbpassword = hiera('profile::djangocms::dbpassword')
  $devday_secret = hiera('profile::djangocms::secret')

  $wsgi_options_hash = {
    user         => 'vagrant',
    group        => 'vagrant',
    processes    => '2',
    threads      => '15',
    display-name => '%{GROUP}',
  }

  apache::vhost { 'devday':
    access_log_file             => 'devday-access.log',
    access_log_format           => 'combined',
    docroot                     => "${basedir}/public",
    error_log_file              => 'devday-error.log',
    port                        => '80',
    servername                  => $vhost,
    wsgi_daemon_process         => 'wsgi_devday',
    wsgi_daemon_process_options => $wsgi_options_hash,
    wsgi_process_group          => 'wsgi_devday',
    wsgi_script_aliases         => { '/' => "${devday_root}/app_init.wsgi", },
  }

  file { "${devday_root}/app_init.wsgi":
    ensure => present,
    content => template('profile/devday/app_init.wsgi.erb'),
  }
}
