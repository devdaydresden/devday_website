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
        that.Events = new EventHandler();
        that.Resize = new ResizeListener();

        that.CSRFHandler = new CSRFHandler();


        // init single class instances
        that.collapse = new ClassInstanceManager('.collapse', 'Collapse');
        that.navbar = new ClassInstanceManager('[data-ui-navbar]', 'Navbar');
    };

    that.addInstances = function ($container) {

        var start = Date.now();

        that.collapse.addInstances($container);
        //that.technicalParameterSearch.addInstances($container);

        console.log('addInstances', Date.now() - start);
    };

    that.startUp();
};


$(document).ready(function () {

    new devdayUIRegistry();
});
