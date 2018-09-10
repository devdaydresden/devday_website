/**
 * trigger class for viewport changes in bootstrap
 *
 * This class provides central handling for viewport changes based on the defined viewports of bootstrap.
 * The 5 supported viewports ar XS, SM, MD, LG and XL. For every viewport there is a defined index from 0 - 4.
 * The needed Index is stored in the appropriate static Members "XS", "SM", "MD", "LG" and "XL".
 *
 * * * * *
 *
 * Initial the class creates 5 hidden divs with the needed bootstrap classes which are stored in the Member "viewDefinitions".
 * According to the displayed element the class decided which viewport is the current one. In the Member "oldViewport" ist the
 * leaved viewport stored.
 *
 * * * * *
 *
 * If you bind a function to the current viewport via addListener the function will be stored in the two-dimensional array "triggers". If
 * you add a listener, which is triggert when you leave a viewport, the functions will be stored in to the two-dimensional array "leaveTriggers".
 * The Functions can be remove by "removeListener" and "removeLeaveListener"
 *
 *
 * e.g. devdayUI.Viewport.addListener(devdayUI.Viewport.SM, Class.triggerMeOnResize);
 * e.g. devdayUI.Viewport.removeListener(devdayUI.Viewport.SM, Class.triggerMeOnResize);
 * e.g. devdayUI.Viewport.addLeaveListener(devdayUI.Viewport.SM, Class.triggerMeOnResize);
 * e.g. devdayUI.Viewport.removeLeaveListener(devdayUI.Viewport.SM, Class.triggerMeOnResize);
 *
 * * * * *
 *
 * Every Triggerfunction gets a eventobject with new current viewport, the oldviewport and the changing direction. The directions can be compared "TOLOWER", "TOUPPER" and to "SAME".
 *
 * e.g. { currentViewport: XXX, oldViewport: XXX, direction: XXX }
 *
 * * * * *
 *
 * Next to this main functionality you can you the function "is" to check if the current viewport is a specified on.
 *
 * e.g. devdayUI.Viewport.is(devdayUI.Viewport.SM); /true / false
 *
 * * * * *
 *
 * The function "isLive" is mostly for internal use in loops. The current viewport will not be set ("setCurrentViewport") in this function to make the check. The function was create for
 * performance reasons in loops.
 *
 * * * * *
 *
 * If you want to compare a specified viewport to the current viewport you can use the "compare" function.
 *
 * e.g. if(devdayUI.Viewport.compare(devdayUI.Viewport.MD) < devdayUI.Viewport.CURRENT) ... // is the MD - Viewport under the current
 * e.g. if(devdayUI.Viewport.compare(devdayUI.Viewport.MD) > devdayUI.Viewport.CURRENT) ... // is the MD - Viewport above the current
 *
 * * * * *
 *
 * The function "triggerViewportFunctions" triggers all functions for the changed viewport. If you resize the window from LG to SM all binded functions for the Viewports LG, MD
 * and SM will be fired. This means all Viewports bitween the start and endviewport will be affected. Not only the old and the new viewport.
 *
 * SIMPLE EXAMPLE

    //Example for Viewport:
    var checkLeaved = function(data) {

        console.log('Leaved ' + devdayUI.Viewport.viewports[data.oldViewport]);
    };

    var check = function(data) {

        console.log('Entered ' + devdayUI.Viewport.viewports[data.currentViewport]);
    };

    devdayUI.Viewport.addLeaveListener(devdayUI.Viewport.MD, checkLeaved);

    devdayUI.Viewport.addListener(devdayUI.Viewport.LG, check);
    devdayUI.Viewport.addListener(devdayUI.Viewport.SM, check);
 *
 */

var ViewportListener = function () {

    'use strict';

    var that = this;

    /**
     * static Vars (DONT TOUCH THIS - else: HAMMERTIME!)
     */
    that.XS = 0;
    that.SM = 1;
    that.MD = 2;
    that.LG = 3;
    that.XL = 4;

    that.TOLOWER = -1;
    that.TOUPPER = 1;
    that.SAME = 0;
    that.CURRENT = 0;

    /**
     * jQuery Vars
     */
    that.$window = $(window);
    that.$body = $('body');

    that.viewports = ['xs', 'sm', 'md', 'lg', 'xl'];
    that.viewDefinitions = ['hidden-sm-up',
        'hidden-md-up hidden-xs-down',
        'hidden-lg-up hidden-sm-down',
        'hidden-xl-up hidden-md-down',
        'hidden-lg-down'];

    that.itemClass = 'responsive-checker-container';
    that.funcClassPrfx = 'responsive-checker-';

    that.bodyClassToUpper = 'viewport-changed-to-upper';
    that.bodyClassToLower = 'viewport-changed-to-lower';

    that.bodyClassCrntViewportPrfx = 'viewport-current-';
    that.bodyClassOldViewportPrfx = 'viewport-old-';

    /**
     * basic Vars
     */
    that.currentViewport = 0;
    that.oldViewport = 0;
    that.triggers = [];
    that.leaveTriggers = [];

    /**
     * basic function to init all
     */
    that.init = function () {
        for (var i = 0, j = that.viewports.length; i < j; ++i) {
            that.$body.append($('<i></i>').addClass(that.itemClass + ' ' + that.funcClassPrfx + that.viewports[i] + ' ' + that.viewDefinitions[i]));
            that.triggers[i] = [];
            that.leaveTriggers[i] = [];
        }

        that.setCurrentViewport();
        that.setBodyClasses(0, that.currentViewport, 1);
        that.$window.resize(that.checkCurrentViewport);
    };

    /**
     * basic function to set class info to the body tag
     */
    that.setBodyClasses = function (oldViewport, currentViewport, direction) {

        /* remove directions classes */
        that.$body.removeClass(that.bodyClassToUpper + ',' + that.bodyClassToLower);

        /* remove old viewport classes */
        that.$body.removeClassByPrefix(that.bodyClassCrntViewportPrfx);

        /* remove current viewport classes */
        that.$body.removeClassByPrefix(that.bodyClassOldViewportPrfx);

        /* add ne classes */
        that.$body.addClass(that.bodyClassCrntViewportPrfx + that.viewports[currentViewport]);
        that.$body.addClass(that.bodyClassOldViewportPrfx + that.viewports[oldViewport]);

        if (direction === that.TOUPPER) {
            that.$body.addClass(that.bodyClassToUpper);
        } else {
            that.$body.addClass(that.bodyClassToLower);
        }
    };

    /**
     * main trigger function which runs on window.resize and calculated which listeners have to be triggert
     */
    that.checkCurrentViewport = function () {

        that.setCurrentViewport();

        var direction = that.currentViewport - that.oldViewport;

        if (Math.abs(direction) > 0) {
            if (direction > 0) { // small to big
                that.triggerViewportFunctions(that.TOUPPER);
            } else { // big to small
                that.triggerViewportFunctions(that.TOLOWER);
            }
        }
    };

    /**
     * trigger function for all current functions assigned to viewport
     */
    that.triggerViewportFunctions = function (direction) {
        for (var i = that.oldViewport, j = that.currentViewport; ((direction < 0) ? i > j : i < j); i = i + direction) {
            var current = i + direction;
            var funcs = that.triggers[current];
            var leaveFuncs = that.leaveTriggers[i];
            var k = 0, l = 0;

            /* trigger leave functions */
            for (k = 0, l = leaveFuncs.length; k < l; ++k) {
                leaveFuncs[k]({
                    currentViewport: current,
                    oldViewport: i,
                    direction: direction
                });
            }

            /* trigger enter functions */
            for (k = 0, l = funcs.length; k < l; ++k) {
                funcs[k]({
                    currentViewport: current,
                    oldViewport: i,
                    direction: direction
                });
            }

            that.setBodyClasses(i, current, direction);
        }
    };

    /**
     * function which checks which ellement is inline visible in sets the current and old viewport
     */
    that.setCurrentViewport = function () {
        that.oldViewport = that.currentViewport;

        for (var i = 0, j = that.viewports.length; i < j; i++) {
            if ($('.' + that.funcClassPrfx + that.viewports[i]).is(':visible')) {
                that.currentViewport = i;
                break;
            }
        }
    };

    /**
     * function which checks if the given viewport is the current
     * e.g. devdayUI.Viewport.is(devdayUI.Viewport.MD)
     */
    that.is = function (vp) {
        that.setCurrentViewport();

        return that.viewports.indexOf(that.viewports[vp]) == that.currentViewport;
    };

    /**
     * function which compares the given viewport with the current
     * e.g. devdayUI.Viewport.compare(devdayUI.Viewport.MD) < devdayUI.Viewport.CURRENT
     */
    that.compare = function (vp) {
        that.setCurrentViewport();

        return that.currentViewport - that.viewports.indexOf(that.viewports[vp]);
    };

    /**
     * function which compares the given viewport with the current without setting currentViewport (internal usage)
     * e.g. devdayUI.Viewport.isLive(devdayUI.Viewport.MD)
     */
    that.isLive = function (vp) {
        return that.viewports.indexOf(that.viewports[vp]) == that.currentViewport;
    };

    /**
     * function to add listener to a viewport
     * e.g. devdayUI.Viewport.addListener(devdayUI.Viewport.SM, Class.triggerMeOnResize);
     */
    that.addListener = function (vp, func) {
        that.triggers[vp].push(func);
    };

    /**
     * function to remove a listener from a viewport
     * e.g. devdayUI.Viewport.removeListener(devdayUI.Viewport.SM, Class.triggerMeOnResize);
     */
    that.removeListener = function (vp, func) {
        var index = that.triggers[vp].indexOf(func);

        if (index > -1) {
            that.triggers[vp].splice(index, 1);
        }
    };

    /**
     * function to add leave listener to a viewport
     * e.g. devdayUI.Viewport.addLeaveListener(devdayUI.Viewport.SM, Class.triggerMeOnResize);
     */
    that.addLeaveListener = function (vp, func) {
        that.leaveTriggers[vp].push(func);
    };

    /**
     * function to remove a leave listener from a viewport
     * e.g. devdayUI.Viewport.removeLeaveListener(devdayUI.Viewport.SM, Class.triggerMeOnResize);
     */
    that.removeLeaveListener = function (vp, func) {
        var index = that.leaveTriggers[vp].indexOf(func);

        if (index > -1) {
            that.leaveTriggers[vp].splice(index, 1);
        }
    };

    that.init();
};
