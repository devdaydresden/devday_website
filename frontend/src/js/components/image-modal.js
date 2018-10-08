/**
 *
 * @param  {[Object]} $element The Element the function fires to
 * @param  {[type]} args     Arguments
 */
var ImageModal = function ($element, args) {

    'use strict';

    var that = this;

    /**
     * jQuery and controll Vars
     */
    that.$baseElement = $element || $('[data-ui-image-modal]');
    that.$element = that.$baseElement;
    that.$imageModal = $('#imageModal');
    that.$modalContent = that.$imageModal.find('.modal-body');
    that.$modalTitle = that.$imageModal.find('.modal-title');
    that.imageSource = that.$element.attr('src');
    that.imageTitle = that.$element.attr('title');


    /**
     * Init of the whole function
     */
    that.initImageModal = function () {
        that.handleClick();
    };

    that.handleClick = function() {
        that.$element.on('click', function () {
            that.setImageToModal();
        });
    };

    that.setImageToModal = function() {
        var img = '<img src="'+that.imageSource+'" />';
        that.$modalContent.html(img);
        that.$modalTitle.html(that.imageTitle);
        that.$imageModal.modal('show');
    }


    that.initImageModal();
};
