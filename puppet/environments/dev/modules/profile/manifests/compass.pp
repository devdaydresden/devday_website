class profile::compass {
  package { ['ruby-devel', 'libffi-devel', 'glibc-devel', 'gcc', 'gcc-c++']:
    ensure => installed,
  } ->
  package { 'compass':
    ensure   => installed,
    provider => 'gem',
  }
}
