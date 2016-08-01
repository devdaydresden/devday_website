class role::devday_runtime {
  include profile::common
  include profile::postgresql_server
  include profile::djangocms
  include profile::wsgi_webserver
}
