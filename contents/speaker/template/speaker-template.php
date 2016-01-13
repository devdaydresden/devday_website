<div class="item">
    <img src="<?php echo $imgURL ?>" alt="<?php echo $name ?>">
    <a href="#modal<?php echo $number ?>" class="hover popup-modal" data-effect="mfp-zoom-in">
        <div>
            <i>
                <svg role="img" fill="currentColor">
                    <use xlink:href="icons/icons.svg#plus-circle"></use>
                </svg>
            </i>
        </div>
        <h6><?php echo $name ?></h6>
    </a>
    <div id="modal<?php echo $number ?>" class="white-popup mfp-hide">
        <div class="row">
            <div class="col-lg-6">
                <img src="<?php echo $imgURL ?>" alt="<?php echo $name ?>">
            </div>
            <div class="col-lg-6">
                <div class="person">
                    <h4><strong><?php echo $name ?></strong></h4>
                    <h5><?php echo $jobDescription ?></h5>
                    <?php echo $speakerText ?>
                    <ul>
                        <?php
                            if(strlen(trim($fbLink)) > 0){
                                echo '<li><a href="'.$fbLink.'"><svg role="img" fill="currentColor"><use xlink:href="icons/icons.svg#face-icon"></use></svg></a></li>';
                            }
                        ?>

                        <?php
                            if(strlen(trim($twLink)) > 0){
                                echo '<li><a href="'.$twLink.'"><svg role="img" fill="currentColor"><use xlink:href="icons/icons.svg#twitter-icon"></use></svg></a></li>';
                            }
                        ?>

                        <?php
                            if(strlen(trim($googleLink)) > 0){
                                echo '<li><a href="'.$googleLink.'"><svg role="img" fill="currentColor"><use xlink:href="icons/icons.svg#google-icon"></use></svg></a></li>';
                            }
                        ?>

                        <?php
                            if(strlen(trim($linkedinLink)) > 0){
                                echo '<li><a href="'.$linkedinLink.'"><svg role="img" fill="currentColor"><use xlink:href="icons/icons.svg#linkedin-icon"></use></svg></a></li>';
                            }
                        ?>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>
