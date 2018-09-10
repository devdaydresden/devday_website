/**
 * [EventHandler triggers custom js events]
 *
 * This class binds / unbinds custom events.
 *
 * Use it like this:
 *  - bind on an Event: devdayUI.Events.bind(devdayUI.Events.EVENTNAME, that.triggerThisOnEvent);
 *  - trigger an Event: devdayUI.Events.trigger(devdayUI.Events.EVENTNAME, [EventsArgs]);
 *
 * Unbind an Event:
 *  - devdayUI.Events.unbind(devdayUI.Events.EVENTNAME, that.triggerThisOnEvent);
 *
 * Define a static EVENTNAME here in the "static Event Vars" area like this:
 *  - that.EVENTNAME = 'eventname';
 *
 * The statics are usefull for same string naming etc.
 *
 */
var EventHandler = function () {

    'use strict';

    var that = this;

    /**
     * static Event Vars
     */
    that.SHOWFLYOUTBACKGROUND = 'showflyoutbackground';


    /**
     * basic Vars
     */
    that.triggers = [];
    that.events = [];

    /**
     * [trigger fires all functions bind to EVENT with ARGS]
     * @param {[string]} event [event name which is triggered]
     * @param {[object]} args [events args]
     */
    that.trigger = function (event, args) {
        if (that.triggers[event] == undefined || that.triggers[event].length === 0) {
            return;
        }

        args = args || {};

        args.event = event;

        for (var i = 0, j = that.triggers[event].length; i < j; ++i) {
            if ($.isFunction(that.triggers[event][i])) {
                that.triggers[event][i](args);
            }
        }
    };

    /**
     * [bind adds a listener to the trigger array when it's added it will be fired on resize]
     * @param {[string]} event [eventname to bind function to it]
     * @param {[function]} func [the function that will be triggert on event trigger
     */
    that.bind = function (event, func) {
        if (that.triggers[event] == undefined) {
            that.triggers[event] = [];
        }
        that.triggers[event].push(func);
    };

    /**
     * [unbind removes a listener from the trigger array so it's not fired anymore on event]
     * @param {[string]} event [eventname to bind function to it]
     * @param {[function]} func [the function that will be triggert on event trigger
     */
    that.unbind = function (event, func) {
        if (that.triggers[event] != undefined) {
            var index = that.triggers[event].indexOf(func);
            if (index < 0) {
                return;
            }
            that.triggers[event].splice(index, 1);
        }
    };
};
