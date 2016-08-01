class profile::devpackages () {
  package { ['libffi-devel', 'glibc-devel', 'gcc', 'gcc-c++', 'libjpeg-devel', 'zlib-devel', 'libpng-devel']:
    ensure => installed,
  }
}