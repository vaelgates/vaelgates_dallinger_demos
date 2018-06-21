/*global $, dallinger, ReconnectingWebSocket */

(function ($, dallinger, ReconnectingWebSocket) {

    var currentNodeId;
    var currentPlayerId;
    // var FILLER_TASK_DURATION_MSECS = 30000
    // var WORD_DISPLAY_DURATION_MSECS = 2000
    // var FETCH_TRANSMISSION_FREQUENCY_MSECS = 100
    var FILLER_TASK_DURATION_MSECS = 3000;
    var WORD_DISPLAY_DURATION_MSECS = 1000;
    var FETCH_TRANSMISSION_FREQUENCY_MSECS = 3000;
    var go = {
        questionnaire: function () {
            dallinger.allowExit();
            dallinger.goToPage("questionnaire");
        }
    };
    var uniqueWords = {
        _words: [],
        add: function (word) {
            word = word.toLowerCase().trim();
            // No empty words
            if (word.length === 0) {
                return false;
            }
            // No words with spaces
            if (word.indexOf(" ") !== -1) {
                return false;
            }
            // No non-unique words
            if (this._words.indexOf(word) !== -1) {
                return false;
            }

            this._words.push(word);
            return word;
        }
    };

    var WordSubmission = (function () {

        /**
         * Tracks turns and handles canditate word submissions.
         */
        var WordSubmission = function (settings) {
            if (!(this instanceof WordSubmission)) {
                return new WordSubmission(settings);
            }
            this.egoID = settings.egoID;
            this._enabled = false;
            this.$button = $("#send-message");
            this.$input = $("#reproduction");
            this._bindEvents();
        };

        WordSubmission.prototype.checkAndSendWord = function () {
            if (! this._enabled) {
                return;
            }
            var self = this;
            var newWord = uniqueWords.add(self.$input.val());
            if (! newWord) {
                return;
            }
            $("#reply").append("<p style='color: #1693A5;'>" + newWord + "</p>");
            self.$input.val("");
            self.$input.focus();

            dallinger.createInfo(
                currentNodeId,
                {contents: newWord, info_type: "Info"}
            ).done(function(resp) {
                self.$button.removeClass("disabled");
                self.$button.html("Send");
            });
        };

        WordSubmission.prototype.changeOfTurn = function (msg) {
            currentPlayerId = msg.player_id;
            if (currentPlayerId === this.egoID) {
                console.log("It's our turn.");
                this._enable();
            } else {
                console.log("It's not our turn.");
                this._disable();
            }
        };

        WordSubmission.prototype._bindEvents = function () {
            var self = this;
            $(document).keypress(function(e) {
                if (e.which === 13) {
                    self.$button.click();
                    return false;
                }
            });
            self.$button.click(function() {
                self.checkAndSendWord();
            });
        };

        WordSubmission.prototype._disable = function () {
            this._enabled = false;
            this.$button.attr("disabled", true);
        };

        WordSubmission.prototype._enable = function () {
            this._enabled = true;
            this.$button.attr("disabled", false);
        };

        return WordSubmission;
    }());

    var ServerSocket = (function () {
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

    $(document).ready(function() {

        var egoParticipantId = dallinger.getUrlParameter("participant_id"),
            wordSubmission = new WordSubmission({egoID: egoParticipantId}),
            callbackMap = {
                "new_word": newWordAdded,
                "change_of_turn": function (msg) { wordSubmission.changeOfTurn(msg); },
            };

        // Leave the chatroom.
        $("#leave-chat").click(function() {
            go.questionnaire();
        });

        ;
        console.log("Starting socket with participantID " + egoParticipantId);
        startSocket(egoParticipantId, callbackMap);
        startPlayer();
    });

    function newWordAdded(msg) {
        console.log("Message is: " + msg);
    }

    function startSocket(playerID, callbackMap) {
        var socketSettings = {
            "endpoint": "chat",
            "broadcast": "memoryexpt2",
            "control": "memoryexpt2_ctrl",
            "lagTolerance": 0.001,
            "callbackMap": callbackMap
        };
        var socket = new ServerSocket(socketSettings);

        socket.open().done(
            function () {
                var data = {
                    type: "connect",
                    player_id: playerID
                };
                socket.send(data);
            }
        );
    }
    // Create the agent.
    function startPlayer() {
        dallinger.createAgent().done(function (resp) {
            currentNodeId = resp.node.id;
            getWordList();
        }).fail(function (rejection) {
            if (rejection.status === 403) {
                return;
            } else {
                dallinger.error(rejection);
            }
        });
    }


    function getWordList() {
        dallinger.get(
            "/node/" + currentNodeId + "/received_infos"
        ).done(function(resp) {
            var wordList = JSON.parse(resp.infos[0].contents);
            showWordList(wordList);
        });
    }

    function showWordList(wl) {
        if (wl.length === 0) {
            // Show filler task.
            showFillerTask();
        } else {
            // Show the next word.
            $("#wordlist").html(wl.pop());
            setTimeout(
                function() {
                    showWordList(wl);
                },
                WORD_DISPLAY_DURATION_MSECS
            );
        }
    }

    function showFillerTask() {
        var filler_answers = [];
        $("#stimulus").hide();
        $("#fillertask-form").show();

        setTimeout(
            function() {
                // store results of filler tasks in array
                $("#fillertask-form input").each(function( i, item ) {
                    filler_answers.push("{" + item.name + ": " + item.value + "}");
                });
                // stores all filler answers in the contents column of info table
                dallinger.createInfo(
                    currentNodeId,
                    {contents: filler_answers.join(", "), info_type: "Info"}
                ).done(function(resp) {
                    showExperiment();
                });
            },
            FILLER_TASK_DURATION_MSECS
        );
    }

    function showExperiment() {
        $("#fillertask-form").hide();
        $("#response-form").show();
        $("#send-message").removeClass("disabled");
        $("#send-message").html("Send");
        $("#reproduction").focus();
        getTransmissions();
    }

    function getTransmissions() {
        dallinger.getTransmissions(
            currentNodeId,
            {status: "pending"}
        ).done(function(resp) {
            console.log("Got transmissions...");
            var transmissions = resp.transmissions;
            for (var i = transmissions.length - 1; i >= 0; i--) {
                displayInfo(currentNodeId, transmissions[i].info_id);
            }
            setTimeout(function () {
                getTransmissions(currentNodeId);
            },
            FETCH_TRANSMISSION_FREQUENCY_MSECS);
        });
    }

    function displayInfo(nodeId, infoId) {
        dallinger.getInfo(
            nodeId, infoId
        ).done(function(resp) {
            var newWord = uniqueWords.add(resp.info.contents);
            if (newWord) {
                $("#reply").append("<p>" + newWord + "</p>");
            }
        });
    }

}($, dallinger, ReconnectingWebSocket));
