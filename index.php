<!DOCTYPE html>

    <html class="no-js" lang="en" xml:lang="en">
    <head>
      <meta charset="utf-8">
      <meta http-equiv="X-UA-Compatible" content="IE=edge">
      <meta name="viewport" content="width=device-width, initial-scale=1"><!-- this is only for responsive design to zoom 100%-->
      <meta name="description" content="A great developer conference from developers for developers">
      <meta name="author" content="Jeremias Arnstadt">
      <link rel="stylesheet" href="css/bootstrap.css">
      <link href='https://fonts.googleapis.com/css?family=Source+Sans+Pro:400,200,300,600,700' rel='stylesheet' type='text/css'>
      <script src="js/libs/modernizr-2.7.1.min.js"></script>

      <link rel="icon" type="image/png" href="favicon.png" />
      <title>DevDay 2016 - Code your world</title>
    </head>

    <body>

        <?php
            include 'lang/de_DE.php';
        ?>

        <div id="preloader"></div>

        <div class="layout">

            <?php include 'contents/header.php' ?>

            <!-- BEGIN MAIN -->

            <div class="mobile-overlay"></div>

            <main id="page-content">

                <?php include 'contents/subheader.php' ?>

                <?php include 'contents/about.php' ?>

                <?php include 'contents/follow.php' ?>

                <?php include 'contents/speaker.php' ?>

                <?php include 'contents/sessions.php' ?>

                <?php include 'contents/sponsors.php' ?>
                <?php include 'contents/contact.php' ?>


                <?php include 'contents/map.php' ?>

                <?php include 'contents/social.php' ?>

            </main>



            <!-- END MAIN -->

            <div class='layout_footer'></div>
        </div>

        <?php include 'contents/footer.php' ?>

        <a id="top" href="#subheader">
            <span>
                <svg role="img" fill="currentColor">
                    <use xlink:href="icons/icons.svg#back-top"></use>
                </svg>
            </span>
        </a>


        <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
        <script src="js/jquery-1.11.2.min.js"></script>
        <!-- Include all compiled plugins (below), or include individual files as needed -->
        <script src="js/bootstrap.min.js"></script>
        <script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"></script>
        <script type="text/javascript" src="http://google-maps-utility-library-v3.googlecode.com/svn/trunk/infobox/src/infobox.js"></script>
        <script src="js/libs/jquery.autosize.js"></script>
        <script src="js/jquery.validate.js"></script>
        <script src="js/jquery.easing.1.3.js"></script>
        <script src="js/jquery.smooth-scroll.min.js"></script>
        <script src="js/jquery.inview.min.js"></script>
        <script src="js/jquery.isotope.min.js"></script>
        <script src="js/masonry.pkgd.min.js"></script>
        <script src="js/jquery.mb.YTPlayer.js"></script>
        <script src="js/jquery.magnific-popup.min.js"></script>
        <script src="js/jquery.animateNumber.min.js"></script>
        <script src="js/owl.carousel.min.js"></script>
        <!-- initial scripts -->
        <script src="js/init.js"></script>

    </body>

</html>

