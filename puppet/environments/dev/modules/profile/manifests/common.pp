class profile::common(
  $dbhostip
) {
  host { 'pgsql':
    ip => $dbhostip
  }
}