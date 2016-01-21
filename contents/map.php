<!-- BEGIN MAP -->

<section class="map" id="anfahrt">

    <div id="map"></div>


    <div id="infobox1">
        <p><strong><?=$mapShowAddress?></strong></p>
    </div>
    <div class="infobox-wrapper">
        <div id="infobox">
            <h2><?=$mapHeadline?></h2>
            <article class="left first">
                <h4><?=$mapHeadline2?></h4>
                <h5><a href="https://www.google.com/maps/d/edit?mid=zBfktBmVT9XI.kY8LsPwquYbs" target="_blank"><?=$mapHeadline3?></a></h5>
            </article>
            <article class="left">
                <ul>
                    <li>
                        <h6 class="normal-headline"><?=$mapAddressHeadline?></h6>
                        <?=$mapAddress?>
                        <div class="clearfix"></div>
                    </li>
                </ul>
            </article>
            <div class="clearfix"></div>

        </div>
    </div>

    <div class="show-mob">

        <article class="left">
            <h2><?=$mapHeadline?></h2>
            <h4><?=$mapHeadline2?></h4>
            <h5><a href="https://www.google.com/maps/d/edit?mid=zBfktBmVT9XI.kY8LsPwquYbs" target="_blank"><?=$mapHeadline3?></a></h5>
        </article>
        <article class="left">
            <ul>
                <li>
                    <h6 class="normal-headline"><?=$mapAddressHeadline?></h6>
                    <?=$mapAddress?>
                    <div class="clearfix"></div>
                </li>
            </ul>
        </article>
        <div class="clearfix"></div>

    </div>

</section>

                <!-- END MAP -->