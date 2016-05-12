<!-- BEGIN FOLLOW -->
<section id="follow" class="follow-section">
  <div class="container">
    <div class="row">
      <div class="col-lg-3 col-md-3">
        <article class="buzz center">
          <a href="https://twitter.com/devdaydresden" class="tweet inline"><span>
            <svg role="img" fill="currentColor">
              <use xlink:href="svgicons/icons.svg#tweet-icon"></use>
            </svg>
          </span></a>
          <h3>#devdaydd</h3>
          <a href="https://twitter.com/devdaydresden" class="btn1 btn--white big follow-btn">FOLGE UNS<span>
            <svg role="img" fill="currentColor">
              <use xlink:href="svgicons/icons.svg#arrow-down"></use>
            </svg>
          </span></a>
        </article>
      </div>
      <div class="col-lg-9 col-md-9">
        <article class="follow-slider">
          <div class="customNavigation">
            <a class="prev"><span>
              <svg fill="currentColor" version="1.1" xmlns="https://www.w3.org/2000/svg" xmlns:xlink="https://www.w3.org/1999/xlink" x="0px" y="0px" width="19px" height="11px" viewBox="0 0 19 11" enable-background="new 0 0 19 11" xml:space="preserve">
                <polygon fill-rule="evenodd" clip-rule="evenodd" points="19,5.25 13.749,0 13,0.75 17.249,5.001 0,5.001 0,6.001 17.248,6.001 13,10.25 13.749,11 19,5.75 "/>
              </svg>
            </span></a>
            <a class="next"><span>
              <svg fill="currentColor" version="1.1" xmlns="https://www.w3.org/2000/svg" xmlns:xlink="https://www.w3.org/1999/xlink" x="0px" y="0px" width="19px" height="11px" viewBox="0 0 19 11" enable-background="new 0 0 19 11" xml:space="preserve">
                <polygon fill-rule="evenodd" clip-rule="evenodd" points="19,5.25 13.749,0 13,0.75 17.249,5.001 0,5.001 0,6.001 17.248,6.001 13,10.25 13.749,11 19,5.75 "/>
              </svg>
            </span></a>
          </div>
          <div id="slider3" class="owl-carousel owl-theme"><?php
$jsonfile = implode(DIRECTORY_SEPARATOR, array(dirname(__FILE__), 'devday2016-tweets.json'));
$tweetdata = json_decode(file_get_contents($jsonfile), $assoc=true);

foreach ($tweetdata['tweets'] as $tweet) { ?>
            <div class="item">
              <div>
                <img src="<?= $tweet['userpic']; ?>" alt="@<?= $tweet['username']; ?>" class="left">
                <h4><?= $tweet['userfullname']; ?></h4>
                <h5 class="light-blue">@<?= $tweet['username']; ?></h5>
              </div>
              <p><?= $tweet['text']; ?></p>
            </div><?php
}
?>
          </div>
        </article>
      </div>
    </div>
  </div>
</section>
<!-- END FOLLOW -->
<?php
// vim: et sw=2 ts=2 ai si
?>
