var CSRFHandler = function () {

    'use strict';

    var that = this;

    /**
     * jquery Vars
     */
    that.forms = $('form');

    that.initCSRF = function () {
        if (typeof session != 'undefined' && typeof session.csrf != 'undefined') {
            session.csrf.value = Cookies.get(session.csrf.cookie);

            console.log(session);

            that.setupAjaxCalls();
            that.addCSRFToForms();
        }
    }

    that.setupAjaxCalls = function () {
        $.ajaxSetup({
            beforeSend: function (xhr) {
                xhr.setRequestHeader(session.csrf.header, session.csrf.value);
            }
        });
    }

    that.addCSRFToForms = function () {
        that.forms.each(function () {
            if (typeof this.method != 'undefined' && this.method.toUpperCase() == "POST") {
                $(this).append('<input type="hidden" name="' + session.csrf.parameter + '" value="' + session.csrf.value + '" />');
            }
        })
    }

    that.initCSRF();
}
