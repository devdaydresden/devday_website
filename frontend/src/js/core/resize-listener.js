/**
 * [ResizeListener trigger class for resize changes in window]
 *
 *
    Example for End
    var resizeEnd = function(event) {
        console.log(event);
    };

    devdayUI.Resize.addEndListener(resizeEnd);
 */
var ResizeListener = function () {

    'use strict';

    var that = this;

    /**
     * jquery Vars
     */
    that.window = $(window);

    /**
     * basic Vars
     */
    that.triggers = [];
    that.instantTriggers = [];
    that.endTriggers = [];
    that.threshold = 112;
    that.endTimeout = null;
    that.endTimeoutTime = 350;
    that.is_keyboard = false;
    that.initial_screen_size = window.innerHeight;

    /**
     * [init basic function to init all]
     */
    that.init = function () {

        $(window).on('resize', function(event){
            that.is_keyboard = (window.innerHeight < that.initial_screen_size);
            that.is_mobile = $('html').hasClass('mobile');
            if (!that.is_keyboard && !that.is_mobile) {
                that.onInstantResize(event);
            } else if (that.is_keyboard && !that.is_mobile) {
                that.onInstantResize(event);
            }
        })
    };

    /**
     * [onResize triggers event on the in the array registered listeners]
     * @param  {[function]} event [the function that will be triggered]
     */
    that.onResize = function (event) {
        for (var i = 0, j = that.triggers.length; i < j; ++i) {
            if ($.isFunction(that.triggers[i])) {
                that.triggers[i](event);
            }
        }
    };

    /**
     * [onInstantResize triggers event on the in the array registered listeners]
     * @param  {[function]} event [the function that will be triggered]
     */
    that.onInstantResize = function (event) {
        for (var i = 0, j = that.instantTriggers.length; i < j; ++i) {
            if ($.isFunction(that.instantTriggers[i])) {
                that.instantTriggers[i](event);
            }
        }
        clearTimeout(that.endTimeout);
        that.endTimeout = setTimeout(function () { that.onResizeEnd(event); }, that.endTimeoutTime);
    };

    /**
     * [onResizeEnd triggers event on the onResizeEnd-Event in the array registered listeners]
     * @param  {[function]} event [the function that will be triggered]
     */
    that.onResizeEnd = function (event) {
        for (var i = 0, j = that.endTriggers.length; i < j; ++i) {
            if ($.isFunction(that.endTriggers[i])) {
                that.endTriggers[i](event);
            }
        }
    };

    /**
     * [addListener adds a listener to the trigger array when it's added it will be fired on resize]
     * @param {[function]} func [the function that will be registered in the trigger array and fired on resize]
     */
    that.addListener = function (func) {
        that.triggers.push(func);
    };

    /**
     * [removeListener removes a listener from the trigger array so it's not fired anymore on resize]
     * @param  {[function]} func [the function which will be removed]
     */
    that.removeListener = function (func) {
        var index = that.triggers.indexOf(func);

        if (index > -1) {
            that.triggers.splice(index, 1);
        }
    };

    /**
     * [addListener adds a listener to the trigger array when it's added it will be fired on resize]
     * @param {[function]} func [the function that will be registered in the trigger array and fired on resize]
     */
    that.addInstantListener = function (func) {
        that.instantTriggers.push(func);
    };

    /**
     * [removeListener removes a listener from the trigger array so it's not fired anymore on resize]
     * @param  {[function]} func [the function which will be removed]
     */
    that.removeInstantListener = function (func) {
        var index = that.instantTriggers.indexOf(func);

        if (index > -1) {
            that.instantTriggers.splice(index, 1);
        }
    };

    /**
     * [addEndListener adds a listener to the trigger array when it's added it will be fired on "resizeend"]
     * @param {[function]} func [the function that will be registered in the trigger array and fired on resize]
     */
    that.addEndListener = function (func) {
        that.endTriggers.push(func);
    };

    /**
     * [removeEndListener removes a listener from the trigger array so it's not fired anymore on "resizeend"]
     * @param  {[function]} func [the function which will be removed]
     */
    that.removeEndListener = function (func) {
        var index = that.endTriggers.indexOf(func);

        if (index > -1) {
            that.triggers.splice(index, 1);
        }
    };

    that.init();
};
