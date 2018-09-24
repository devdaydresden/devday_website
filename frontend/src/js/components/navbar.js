/**
 *
 * @param  {[Object]} $element The Element the function fires to
 * @param  {[type]} args     Arguments
 */
var Navbar = function ($element, args) {

    'use strict';

    var that = this;

    /**
     * jQuery and controll Vars
     */
    that.$baseElement = $element || $('[data-ui-navbar]');
    that.$element = that.$baseElement;
    that.$body = $('body');


    /**
     * Init of the whole function
     */
    that.initNavbar = function () {
        that.$body.scrollspy({
            target: '#mainNav',
            offset: 57
        });

        $(window).on('scroll',function(){that.navbarHandle()});

        that.navbarHandle();
    };

    that.navbarHandle = function () {
        if (that.$element.offset().top > 54) {
            that.$element.addClass("navbar-shrink");
        } else {
            that.$element.removeClass("navbar-shrink");
        }
    }


    that.initNavbar();

};



