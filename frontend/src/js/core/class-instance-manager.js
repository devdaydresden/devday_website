/**
*
* User to generate dynamic multi instances of single component classes
*
* This class takes a data-tag attribute to find the root html containers of the controle and initilise the functionality
* by the given classname. If you need special arguments to init the component-class use the args variable. it will be the second
* param in the constuctor class. the first is the root element of the control.
*
* All instances of the given class will be write into the array "instances".
*
*/
var ClassInstanceManager = function(dataTag, className, args) {

    'use strict';

    var that = this;

    /**
    * Basic vars
    */
    that.instances  = [];
    that.dataTag     = dataTag;
    that.className   = className;
    that.initDataTag = 'data-component-init';

    /**
    * Bind Function
    */
    that.generateInstances = function() {

        var start = Date.now();
        var count = 0;
        var tag   = that.initDataTag + that.className;

        $(that.dataTag).each(function(index) {

            var $element = $(this);
            var isInit   = $element.attr(tag) !== undefined;

            if(isInit) {
                console.log('already init');
                return;
            }
            $element.attr(tag, 1);
            that.instances.push(new window[that.className]($element, args));
            ++count;
        });


        console.log(that.className + ' (' + count + ')', Date.now() - start);
    };

    /**
    * add Function
    */
    that.addInstances = function($container) {
        var start2 = Date.now();
        var count2 = 0;
        $container.find(that.dataTag).each(function(index) {
            that.instances.push(new window[that.className]($(this), args));
        });

        //check for parent container
        if ($container.is(that.dataTag)) {
            that.instances.push(new window[that.className]($container, args));
        }
        console.debug('addInstances: '+that.dataTag + ' (' + count2 + ')', Date.now() - start2);
    };

    /**
    * call Functions func with args in every instance
    */
    that.call = function(func, args) {
        for(var i = 0, j = that.instances.length; i < j; ++i) {
            if(typeof that.instances[i][func] === 'function') {
                that.instances[i][func](args);
            }
        }
    };

    that.generateInstances();
};
