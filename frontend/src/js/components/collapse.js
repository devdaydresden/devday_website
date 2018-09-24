/**
 *
 * @param  {[Object]} $element The Element the function fires to
 * @param  {[type]} args     Arguments
 */
var navbarCollapse = function ($element, args) {

    'use strict';

    var that = this;

    /**
     * jQuery and controll Vars
     */
    that.$baseElement = $element || $('.navbar-collapse');
    that.$element = that.$baseElement;
    that.$navbar = $('nav.navbar');


    /**
     * Init of the whole function
     */
    that.initNavbarCollapse = function () {
        that.$element.on('show.bs.collapse', function(){
            that.$navbar.addClass('navbar-shrink');
        })

        that.$element.on('hidden.bs.collapse', function(){
            if (that.$navbar.offset().top < 54) {
                that.$navbar.removeClass('navbar-shrink');
            }
        })
    };


    that.initNavbarCollapse();
};
