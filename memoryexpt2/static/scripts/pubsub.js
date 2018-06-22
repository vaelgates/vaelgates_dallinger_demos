/*global $, ReconnectingWebSocket */

var pubsub = (function ($, ReconnectingWebSocket) {

    var backend = {};

    backend.Socket = (function () {
        var makeSocket = function (endpoint, channel, tolerance) {
            var ws_scheme = (window.location.protocol === "https:") ? "wss://" : "ws://",
                app_root = ws_scheme + location.host + "/",
                socket;

            socket = new ReconnectingWebSocket(
                app_root + endpoint + "?channel=" + channel + "&tolerance=" + tolerance
            );
            socket.debug = true;

            return socket;
        };

        var dispatch = function (self, event) {
            var marker = self.broadcastChannel + ":";
            if (event.data.indexOf(marker) !== 0) {
                console.log(
                    "Message was not on channel " + self.broadcastChannel + ". Ignoring.");
                return;
            }
            var msg = JSON.parse(event.data.substring(marker.length));

            var callback = self.callbackMap[msg.type];
            if (typeof callback !== "undefined") {
                callback(msg);
            } else {
                console.log("Unrecognized message type " + msg.type + " from backend.");
            }
        };

        /*
         * Public API
         */
        var Socket = function (settings) {
            if (!(this instanceof Socket)) {
                return new Socket(settings);
            }

            var self = this,
                tolerance = typeof(settings.lagTolerance) !== "undefined" ? settings.lagTolerance : 0.1;

            this.broadcastChannel = settings.broadcast;
            this.controlChannel = settings.control;
            this.callbackMap = settings.callbackMap;


            this.socket = makeSocket(
                settings.endpoint, this.broadcastChannel, tolerance);

            this.socket.onmessage = function (event) {
                dispatch(self, event);
            };
        };

        Socket.prototype.open = function () {
            var isOpen = $.Deferred();

            this.socket.onopen = function (event) {
                isOpen.resolve();
            };

            return isOpen;
        };

        Socket.prototype.send = function (data) {
            var msg = JSON.stringify(data),
                channel = this.controlChannel;

            console.log("Sending message to the " + channel + " channel: " + msg);
            this.socket.send(channel + ":" + msg);
        };

        Socket.prototype.broadcast = function (data) {
            var msg = JSON.stringify(data),
                channel = this.broadcastChannel;

            console.log("Broadcasting message to the " + channel + " channel: " + msg);
            this.socket.send(channel + ":" + msg);
        };

        return Socket;
    }());


    return backend;


}($, ReconnectingWebSocket));
