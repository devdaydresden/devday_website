<!-- BEGIN Speaker -->
<section id="speaker" class="speaker-section">
  <article class="background-img">
    <div class="container">
      <h3 class="dark-blue">Speaker</h3>
      <p class="center">Eingeladen waren Sprecher aus ganz Deutschland, um zu
      aktuellen Themen in der Softwarearchitektur und -entwicklung  Vorträge zu
      halten und mit Euch gemeinsam über Trends zu diskutieren.<br />
      Mit Dave Farley war diesmal auch ein bekannter internationaler Sprecher
      dabei.</p>
    </div>
  </article>
  <div class="container">
    <div class="slider-wrap-speaker">
      <div id="owl2" class="owl-carousel owl-theme"><?php
$jsonfile = implode(DIRECTORY_SEPARATOR, array(dirname(__FILE__), 'devday2016-speakers.json'));
$speakerdata = json_decode(file_get_contents($jsonfile), $assoc=true);
$jsonfile = implode(DIRECTORY_SEPARATOR, array(dirname(__FILE__), 'devday2016-sessions.json'));
$sessiondata = json_decode(file_get_contents($jsonfile), $assoc=true);

function find_sessions($sessiondata, $sessionids) {
  $retval = array();
  foreach ($sessiondata as $time => $talks) {
    foreach ($talks as $talk) {
      if (array_key_exists("id", $talk) && in_array($talk['id'], $sessionids)) {
        $retval[] = array('title' => $talk['description'], 'text' => $talk['text']);
      }
    }
  }
  return $retval;
}

$number = 0;
foreach ($speakerdata['speakers'] as $speaker) {
  $number++;
  $sessions = find_sessions($sessiondata, $speaker['sessions']);
  $session_names = array();
  foreach ($sessions as $session) {
    $session_names[] = $session['title'];
  }
?>
        <div class="item">
          <img src="contents/speaker/images/<?= $speaker['img']; ?>" alt="<?= $speaker['name']; ?>">
          <a href="#modal<?= $number ?>" class="hover popup-modal" data-effect="mfp-zoom-in">
            <div>
              <i>
                <svg role="img" fill="currentColor">
                  <use xlink:href="svgicons/icons.svg#plus-circle"></use>
                </svg>
              </i>
            </div>
            <h6><?= $speaker['name']; ?></h6>
          </a>
          <div id="modal<?= $number; ?>" class="white-popup mfp-hide">
            <div class="row">
              <div class="col-lg-6">
                <img src="contents/speaker/images/<?= $speaker['img']; ?>" alt="<?= $speaker['name']; ?>">
              </div>
              <div class="col-lg-6">
                <div class="person">
                  <h4><strong><?= $speaker['name']; ?></strong></h4>
                  <h5><?= $speaker['profession']; ?><br /><?php
                    print((count($session_names) > 1) ? "Sessions" : "Session"); ?>: <?= implode(", ", $session_names); ?>
                  </h5>
                  <div class="accordion" id="accordion<?= $number; ?>">
                    <div class="accordion-group">
                      <div class="accordion-heading">
                        <a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion<?= $number; ?>" href="#collapseOne<?= $number; ?>">Zur Person</a>
                      </div>
                      <div id="collapseOne<?= $number; ?>" class="accordion-body collapse in">
                        <div class="accordion-inner"><?= $speaker['information']; ?></div>
                      </div>
                    </div>
                    <div class="accordion-group">
                      <div class="accordion-heading">
                        <a class="accordion-toggle collapsed" data-toggle="collapse" data-parent="#accordion<?= $number; ?>" href="#collapseTwo<?= $number; ?>">Sessioninformationen</a>
                      </div>
                      <div id="collapseTwo<?= $number; ?>" class="accordion-body collapse">
                      <div class="accordion-inner"><?php
                      foreach ($sessions as $session) {
                        if (count($sessions) > 1) {
                          ?><p><strong><?= $session['title']; ?></strong></p><?php
                        } ?><?= $session['text']; ?><?php
                      } ?></div>
                      </div>
                    </div>
                  </div>
                  <ul><?php
if (array_key_exists("facebook", $speaker['ids'])) {
  printf('<li><a href="%s"><svg role="img" fill="currentColor"><use xlink:href="svgicons/icons.svg#face-icon"></use></svg></a></li>', $speaker['ids']['facebook']);
}
if (array_key_exists("twitter", $speaker['ids'])) {
  printf('<li><a href="https://twitter.com/%s"><svg role="img" fill="currentColor"><use xlink:href="svgicons/icons.svg#twitter-icon"></use></svg></a></li>', $speaker['ids']['twitter']);
}
if (array_key_exists('google', $speaker['ids'])) {
  printf('<li><a href="%s"><svg role="img" fill="currentColor"><use xlink:href="svgicons/icons.svg#google-icon"></use></svg></a></li>', $speaker['ids']['google']);
}
if (array_key_exists('linkedin', $speaker['ids'])) {
  printf('<li><a href="%s"><svg role="img" fill="currentColor"><use xlink:href="svgicons/icons.svg#linkedin-icon"></use></svg></a></li>', $speaker['ids']['linkedin']);
}
?></ul>
                </div>
              </div>
            </div>
          </div>
        </div><?php
} ?>
      </div>
    </div>
  </div>
</section>
<!-- END Speaker -->
<?php
// vim: et sw=2 ts=2 ai si
?>
