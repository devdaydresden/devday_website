class profile::djangolocal () {
  firewalld_port { 'Open port 8000 access':
    ensure => 'present',
    zone => 'public',
    port => 8000,
    protocol => 'tcp',
  }
}