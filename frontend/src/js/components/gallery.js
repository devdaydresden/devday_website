/**
 *
 * @param  {[Object]} $element The Element the function fires to
 * @param  {[type]} args     Arguments
 */
var Gallery = function ($element, args) {

    'use strict';

    var that = this;

    /**
     * jQuery and controll Vars
     */
    that.$baseElement = $element || $('[data-ui-gallery]');
    that.$element = that.$baseElement;

    /**
     * Init of the whole function
     */
    that.initGallery = function () {
        baguetteBox.run('[data-ui-gallery]');
    };


    that.initGallery();
};
