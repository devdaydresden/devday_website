class profile::compass {
  include profile::devpackages

  package { 'ruby-devel':
    ensure => installed,
  }

  package { 'compass':
    ensure   => installed,
    provider => 'gem',
    require  => [
      Package['ruby-devel'], Package['libffi-devel'], Package['glibc-devel'], Package['gcc'], Package['gcc-c++']
    ]
  }
}
