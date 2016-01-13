<!-- BEGIN Speaker -->

<section id="speaker" class="speaker-section">

    <article class="background-img">
        <div class="container">

            <h3 class="dark-blue"><?=$speakerHeadline?></h3>
            <p class="center"><?=$speakerText?> </p>

        </div>
    </article>

    <div class="container">

        <div class="slider-wrap-speaker">

            <div id="owl2" class="owl-carousel owl-theme ">
                <?php
                $number = 0;
                foreach (glob("contents/speaker/*.php") as $filename)
                {
                    $number++;
                    include $filename;
                }
                ?>
            </div>

        </div>

    </div>

</section>

<!-- END Speaker -->