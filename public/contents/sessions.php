<?php
function slideshare_url($link, $user) {
    return sprintf("//www.slideshare.net/%s/%s", $user, $link);
}

function slideshare_iframe($key, $link, $title, $width=595, $height=485, $user = "devday-dd", $usertitle="DevDay Dresden") {
?><iframe src="//www.slideshare.net/slideshow/embed_code/key/<?= $key ?>" width="595" height="485" frameborder="0" marginwidth="0" marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px; margin-bottom:5px; max-width: 100%;" allowfullscreen> </iframe>
    <p class="slideref"><a href="<?= slideshare_url($link, $user); ?>" title="<?= $title; ?>" target="_blank"><?= $title; ?></a> from <a href="//www.slideshare.net/<?= $user; ?>" target="_blank"><?= $usertitle; ?></a></div><?php
}

$session_data = array(
    "12:00 - 13:00" => array(
        array(
            "description" => "Anmeldung"
        ),
    ),
    "13:00 - 13:15" => array(
        array(
            "room" => "Hamburg",
            "description" => "Eröffnung durch Prof. Frank Schönefeld"
        ),
    ),
    "13:15 - 14:15" => array(
        array(
            "room" => "Hamburg",
            "description" => "Keynote (Englisch): The Rationale for Continuous Delivery",
            "speaker" => "Dave Farley",
            "slideshare" => array(
                "key" => "LIydla0m0gTfnP",
                "link" => "devday-2016-dave-farley-the-rationale-for-continuous-delivery",
                "title" => "DevDay 2016: Dave Farley - The Rationale for Continuous Delivery",
            ),
        ),
    ),
    "14:15 - 14:30" => array(
        array(
            "description" => "kurze Pause",
        ),
    ),
    "14:30 - 15:15" => array(
        array(
            "description" => "DevOps - Microsoft Developer Divisions Weg ins nächste Agile Zeitalter",
            "speaker" => "Artur Speth",
            "room" => "Hamburg",
//                <iframe src="//www.slideshare.net/slideshow/embed_code/key/MOZ1ZKmgwcWaOU" width="595" height="485" frameborder="0" marginwidth="0" marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px; margin-bottom:5px; max-width: 100%;" allowfullscreen> </iframe> <div style="margin-bottom:5px"> <strong> <a href="//www.slideshare.net/devday-dd/devday-2016-artur-speth-devops-microsoft-developer-divisions-weg-ins-nchste-agile-zeitalter" title="DevDay 2016: Artur Speth - DevOps - Microsoft Developer Divisions Weg ins nächste Agile Zeitalter" target="_blank">DevDay 2016: Artur Speth - DevOps - Microsoft Developer Divisions Weg ins nächste Agile Zeitalter</a> </strong> from <strong><a href="//www.slideshare.net/devday-dd" target="_blank">DevDay Dresden</a></strong> </div>
        ),
        array(
            "description" => "Continuous Delivery - Aber Sicher?!",
            "speaker" => "Jan Dittberner",
            "room" => "Gartensaal",
            // <iframe src="//www.slideshare.net/slideshow/embed_code/key/3GppXjxcDaAOik" width="595" height="485" frameborder="0" marginwidth="0" marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px; margin-bottom:5px; max-width: 100%;" allowfullscreen> </iframe> <div style="margin-bottom:5px"> <strong> <a href="//www.slideshare.net/devday-dd/devday-2016-jan-dittberner-continous-delivery-aber-sicher" title="DevDay 2016 - Jan Dittberner - Continous Delivery - Aber sicher?!" target="_blank">DevDay 2016 - Jan Dittberner - Continous Delivery - Aber sicher?!</a> </strong> from <strong><a href="//www.slideshare.net/devday-dd" target="_blank">DevDay Dresden</a></strong> </div>
        ),
        array(
            "description" => "Lose gekoppelt wie nie: DI vs. IoC",
            "speaker" => "Hendrik Lösch",
            "room" => "St. Petersburg",
        ),
    ),
    "15:15 - 15:45" => array(
        array(
            "description" => "Kaffeepause",
        ),
    ),
    "15:45 - 16:30" => array(
        array(
            "description" => "Acceptance Testing for Continuous Delivery",
            "speaker" => "Dave Farley",
            "room" => "Hamburg",
        ),
        array(
            "description" => "MIXING UP REALITIES – Mit AR, VR, AV zu neuen Realitäten",
            "speaker" => "Frank Lamack & Denis Loh",
            "room" => "Gartensaal",
        ),
        array(
            "description" => "Testautomatisierungsframework Xeta",
            "speaker" => "Peter Lehmann",
            "room" => "St. Petersburg",
        ),
    ),
    "16:30 - 16:45" => array(
        array(
            "description" => "kurze Pause",
        ),
    ),
    "16:45 - 17:30" => array(
        array(
            "description" => "Sicherheit der Dinge – \"Hacking im IoT\"",
            "speaker" => "Thomas Haase",
            "room" => "Hamburg",
        ),
        array(
            "description" => "Kleine Änderungen - enorme Wirkung: Datenbank-Coding für den Echtbetrieb",
            "speaker" => "Carsten Czarski",
            "room" => "Gartensaal",
        ),
        array(
            "description" => "Cloud-Umgebungen mit Terraform verwalten",
            "speaker" => "Sascha Askani",
            "room" => "St. Petersburg",
        ),
    ),
    "17:30 - 17:45" => array(
        array(
            "description" => " kurze Pause",
        ),
    ),
    "17:45 - 18:45" => array(
        array(
            "description" => "Eine sprachneutrale Essenz der Microservices",
            "speaker" => "Adam Bien",
            "room" => "Hamburg"
        ),
    ),
    "18:45 - 20:30" => array(
        array(
            "description" => "Get together",
        ),
    ),
);

?>
<!-- START SESSIONS -->
<section id="sessions" class="sessions-section ">

    <div class="container">

        <h4><a href="https://lineupr.com/saec/devday16">Sessionplan in der Webapp öffnen</a></h4>

        <h3 data-toggle="collapse"  data-target="#sessionCollapse" aria-expanded="false" aria-controls="sessionCollapse">
            Zeige Sessions
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

    <h3 data-toggle="collapse" data-target="#slidesCollapse" aria-expanded="false" aria-controls="slidesCollapse">
        Zeige Slides
        <i class="fa fa-angle-down"></i>
    </h3>

    <div class="collapse" id="slidesCollapse">
<div class="container"><?php
foreach ($session_data as $time => $talks) {
    foreach ($talks as $talk) {
        if (array_key_exists("slideshare", $talk)) {
            $info = $talk["slideshare"]; ?>
<div class="row">
    <div class="col-sm-12 col-md-12 col-lg-12 devday__item">
        <div class="center">
<?php
            slideshare_iframe($info["key"], $info["link"], $info["title"]); ?>
        </div>
    </div>
</div>
<?php
        }
    }
} ?></div></div>

</section>

                <!-- END SESSIONS -->
