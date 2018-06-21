/*global $, dallinger, ReconnectingWebSocket */

(function ($, dallinger, ReconnectingWebSocket) {

    var currentNodeId;
    var currentPlayerId;
    var egoParticipantId;
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
                isOpen = $.Deferred(),
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

        // Send a message.
        $("#send-message").click(function() {
            checkAndSendWord();
        });

        // Leave the chatroom.
        $("#leave-chat").click(function() {
            go.questionnaire();
        });

        if ($("#experiment").length > 0) {
            egoParticipantId = dallinger.getUrlParameter("participant_id");
            console.log("Starting socket with participantID " + egoParticipantId);
            startSocket(egoParticipantId);
            startPlayer();
        }
    });

    function newWordAdded(msg) {
        console.log("Message is: " + msg);
    }

    function changeOfTurn(msg) {
        console.log("Message is: " + msg);
        currentPlayerId = msg.player_id;
        if (currentPlayerId === egoParticipantId) {
            $("#send-message").attr("disabled", false);
        } else {
            $("#send-message").attr("disabled", true);
        }
        console.log("Updated turn to " + currentPlayerId);
    }

    function startSocket(player_id) {
        var socketSettings = {
            "endpoint": "chat",
            "broadcast": "memoryexpt2",
            "control": "memoryexpt2_ctrl",
            "lagTolerance": 0.001,
            "callbackMap": {
                "new_word": newWordAdded,
                "change_of_turn": changeOfTurn,
            }
        };
        var socket = new ServerSocket(socketSettings);

        socket.open().done(
            function () {
                var data = {
                    type: "connect",
                    player_id: player_id
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

    function checkAndSendWord() {
        // #reproduction is the typing box
        var newWord = uniqueWords.add($("#reproduction").val());
        if (! newWord) {
            return;
        }
        $("#reply").append("<p style='color: #1693A5;'>" + newWord + "</p>"); //MONICA
        $("#reproduction").val("");
        $("#reproduction").focus();

        dallinger.createInfo(
            currentNodeId,
            {contents: newWord, info_type: "Info"}
        ).done(function(resp) {
            $("#send-message").removeClass("disabled");
            $("#send-message").html("Send");
        });
    }

    $(document).keypress(function(e) {
        if (e.which === 13) {
            $("#send-message").click();
            return false;
        }
    });

}($, dallinger, ReconnectingWebSocket));
