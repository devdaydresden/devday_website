<?php
# vim: sw=4 ts=4 et
function slideshare_url($link, $user) {
    return sprintf("//www.slideshare.net/%s/%s", $user, $link);
}

function slideshare_iframe($key, $link, $title, $width=595, $height=485, $user = "devday-dd", $usertitle="DevDay Dresden") {
  return sprintf(
    '<iframe src="//www.slideshare.net/slideshow/embed_code/key/%s" width="%d" height="%d" frameborder="0" marginwidth="0" ' .
    'marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px; margin-bottom:5px; max-width: 100%%;" ' .
    'allowfullscreen> </iframe><p class="slideref"><a href="%s" title="%s" target="_blank">%s</a> from ' .
    '<a href="//www.slideshare.net/%s" target="_blank">%s</a></p>',
    $key, $width, $height, $link, $title, $title, $user, $usertitle
  );
}

function youtube_iframe($key) {
  return sprintf('<iframe width="560" height="315" src="https://www.youtube.com/embed/%s" frameborder="0" allowfullscreen></iframe>', $key);
}

function talk_feedback($text) {
  return sprintf('<blockquote>%s</blockquote>', $text);
}

function accordion_group($number, $title, $text, $subnum, $collapsed=true) {
  return sprintf('<div class="accordion-group">
  <div class="accordion-heading">
    <a class="accordion-toggle%s" data-toggle="collapse" data-parent="#accordion%d" href="#collapse%s%d">%s <i class="fa fa-angle-down pull-right"></i><i class="fa fa-angle-up pull-right"></i></a>
  </div>
  <div id="collapse%s%d" class="accordion-body collapse%s">
    <div class="accordion-inner">%s</div>
  </div>
</div>', $collapsed ? ' collapsed' : '', $number, $subnum, $number, $title, $subnum, $number, $collapsed ? '' : ' in', $text);
}

$jsonfile = implode(
    DIRECTORY_SEPARATOR,
    array(dirname(__FILE__), 'devday2016-sessions.json'));
$session_data = json_decode(file_get_contents($jsonfile), $assoc=true);

$jsonfile = implode(
    DIRECTORY_SEPARATOR,
    array(dirname(__FILE__), 'devday2016-slides.json'));
$slides_data = json_decode(file_get_contents($jsonfile), $assoc=true);

?><!-- START SESSIONS -->
<section id="sessions" class="sessions-section ">
  <!--<div class="container">
    <h3 data-toggle="collapse"  data-target="#sessionCollapse" aria-expanded="false" aria-controls="sessionCollapse">
      Zeige Sessionplan
      <i class="fa fa-angle-down"></i>
    </h3>
    <div class="collapse" id="sessionCollapse">
      <table>
        <thead>
          <tr>
            <th style="min-width:135px">Zeit</th>
            <th></th>
            <th></th>
            <th></th>
          </tr>
        </thead>
        <tbody><?php
foreach ($session_data as $time => $talks) {
                    ?><tr><td><?= $time; ?></td><?php
    foreach ($talks as $talk) {
        ?><td<?php if (count($talks) === 1) { ?> colspan="3"<?php } ?> class="align-center"><?= $talk["description"]; ?><?php
        if (array_key_exists("speaker", $talk)) {
            ?><p class="hint"><strong><?= $talk["speaker"]; ?></p><?php
        }
        if (array_key_exists("room", $talk)) {
            ?><p class="hint italic"><i class="fa fa-arrow-circle-o-down"></i> Raum: <?= $talk["room"]; ?></p><?php
        } ?></td><?php
    } ?></tr><?php
} ?></tbody>
      </table>
    </div>
  </div>-->
  <div class="container">
    <div class="row">
      <div class="col-lg-12 col-md-12 col-sm-12">
        <h4>Hier findet ihr die Vortragsfolien und Videos zu den DevDay 2016-Vorträgen:</h4>
        <div class="slider-wrap-slides">
          <div id="owl3" class="owl-carousel owl-theme"><?php
foreach ($session_data as $time => $talks) {
    foreach ($talks as $talk) {
        if (array_key_exists('slideshare', $talk) or array_key_exists('youtube', $talk) or array_key_exists('feedback', $talk)) {
            $number++;
            $data = array();
            if (array_key_exists('slideshare', $talk)) {
                $key = $talk['slideshare']['key'];
                $info = $slides_data[$key];
                $data[] = accordion_group($number, 'Vortragsfolien', slideshare_iframe($key, $info['url'], $info['title']), 'Slides');
            }
            if (array_key_exists('youtube', $talk)) {
                $key = $talk['youtube']['key'];
                $data[] = accordion_group($number, 'Video', youtube_iframe($key), 'Video', true);
            }
            if (array_key_exists('feedback', $talk)) {
                $data[] = accordion_group($number, 'Zusammenfassung', talk_feedback($talk['feedback']), 'Feedback', true);
            } ?>
            <div class="item">
                <h4 class="session-name"><?= $talk["description"]; ?></h4>
                <div class="accordion session_accordion" id="accordion<?= $number; ?>"><?php print(implode($data)); ?></div>
            </div><?php
        }
    }
} ?></div>
        </div>
      </div>
    </div>
  </div>
</section>
<!-- END SESSIONS -->
<?php
// vim: et sw=2 ts=2 ai si
?>
