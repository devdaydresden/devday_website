<?php
function slideshare_url($link, $user) {
    return sprintf("//www.slideshare.net/%s/%s", $user, $link);
}

function slideshare_iframe($key, $link, $title, $width=595, $height=485, $user = "devday-dd", $usertitle="DevDay Dresden") {
?><iframe src="//www.slideshare.net/slideshow/embed_code/key/<?= $key ?>" width="595" height="485" frameborder="0" marginwidth="0" marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px; margin-bottom:5px; max-width: 100%;" allowfullscreen> </iframe>
    <p class="slideref"><a href="<?= $link; ?>" title="<?= $title; ?>" target="_blank"><?= $title; ?></a> from <a href="//www.slideshare.net/<?= $user; ?>" target="_blank"><?= $usertitle; ?></a></p><?php
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
  <div class="container">
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
} ?>
        </tbody>
      </table>
    </div>
  </div>
  <div class="container">
    <div class="row">
      <div class="col-lg-12 col-md-12 col-sm-12">
        <p class="center">Hier findet ihr die Vortragsfolien zu den DevDay 2016-Vorträgen:</p>
        <div class="slider-wrap-slides">
          <div id="owl3" class="owl-carousel owl-theme"><?php
foreach ($session_data as $time => $talks) {
    foreach ($talks as $talk) {
        if (array_key_exists("slideshare", $talk)) {
          $key = $talk['slideshare']['key'];
          $info = $slides_data[$key];?>
            <div class="item"><?php slideshare_iframe($key, $info["url"], $info["title"]); ?></div>
<?php
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
