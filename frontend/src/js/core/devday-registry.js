/**
 * create class instances in correct order
 *
 * This class creates the main namespace for this application. All necessary components will be initialised in the
 * "startUp" method and bound to "window.devdayUI".
 */
var devdayUIRegistry = function () {

    'use strict';

    var that = this;

    //core classes
    that.Viewport = null;
    that.Resize = null;
    that.Events = null;

    //single classes
    that.collapse = null;


    that.startUp = function () {

        // bind this class to window.devdayUI
        window.devdayUI = that;

        // init core classes
        that.Viewport = new ViewportListener();
        that.Events = new EventHandler();
        that.Resize = new ResizeListener();

        that.CSRFHandler = new CSRFHandler();


        // init single class instances
        that.collapse = new ClassInstanceManager('.collapse', 'Collapse');
    };

    that.addInstances = function ($container) {

        var start = Date.now();

        that.tabbed.addInstances($container);
        that.FormValidate.addInstances($container);
        that.tableResponsive.addInstances($container);
        that.advancedTableResponsive.addInstances($container);
        that.teaserCarousel.addInstances($container);
        that.responsiveImage.addInstances($container);
        that.navigationElementlist.addInstances($container);
        that.navigationElementlistButtons.addInstances($container);
        that.carousel.addInstances($container);
        that.maps.addInstances($container);
        that.slider.addInstances($container);
        that.instantSubmit.addInstances($container);
        that.autocomplete.addInstances($container);
        that.collapse.addInstances($container);
        //that.technicalParameterSearch.addInstances($container);

        console.log('addInstances', Date.now() - start);
    };

    that.startUp();
};


$(document).ready(function () {

    new devdayUIRegistry();
});
