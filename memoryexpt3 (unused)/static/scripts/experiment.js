/*global $, dallinger, pubsub, settings */

(function ($, dallinger, pubsub, settings) {

    var currentNodeId;
    var currentPlayerId;
    var FILLER_TASK_DURATION_MSECS = 30000;
    var WORD_DISPLAY_DURATION_MSECS = 2000;
//     var FILLER_TASK_DURATION_MSECS = 3000; // for testing
//     var WORD_DISPLAY_DURATION_MSECS = 100; // 100 for testing

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
        },

        /**
         * Return a copy of the word list.
         */
        retrieve: function () {
            return this._words.slice();
        }
    };

    var Timer = (function () {

        /**
         * Displays seconds remaining in the current turn, and indicates
         * whether it's the current player's turn, or some other player's.
         */
        var Timer = function (options) {
            if (!(this instanceof Timer)) {
                return new Timer(options);
            }
            this.egoID = options.egoID;
            this.socket = options.socket;
            this.$turnIndicator = $("#turn-info");
            this.$timeRemaining = $("#time-remaining");
            this._timeoutID = null;
            this.socket.subscribe(this.changeOfTurn, "change_of_turn", this);
        };

        Timer.prototype.reset = function (seconds) {
            this.stop();
            this.set(seconds);
        };

        Timer.prototype.set = function (seconds) {
            var self = this;

            this.showTimeRemaining(seconds);
            this._timeoutID = setInterval(
                function () {
                    seconds--;
                    self.showTimeRemaining(seconds);
                    if (seconds <= 0) {
                        self.stop();
                    }
                },
                1000
            );
        };

        Timer.prototype.stop = function () {
            clearInterval(this._timeoutID);
        };

        Timer.prototype.showWhosTurn = function (currentPlayerId) {
            if (currentPlayerId === this.egoID) {
                return "<span class='active-turn'>It's your turn!</span>";
            } else {
                return "It's someone else's turn.";
            }
        };

        Timer.prototype.showTimeRemaining = function (seconds) {
            this.$timeRemaining.html(seconds + " seconds remaining...");
        };

        Timer.prototype.changeOfTurn = function (msg) {
            this.$turnIndicator.html(this.showWhosTurn(msg.player_id));
            this.reset(msg.turn_seconds);
        };

        return Timer;
    }());

    var Word = (function () {

        /**
         * Displays or reads a word submitted by another player.
         */
        var Word = function (options) {
            if (!(this instanceof Word)) {
                return new Word(options);
            }
            this.message = options.message;
            this.word = options.message.word;
            this.egoID = options.egoID;
            this.wordsAloud = options.wordsAloud;
            this.voice = speechSynthesis.getVoices().filter(
                function (voice) { return voice.name === "Alex"; }
            )[0];
        };

        Word.prototype.isIntendedForMe = function () {
            return this.message.recipients.indexOf(this.egoID) !== -1;
        };

        Word.prototype.print = function () {
            return "<p>" + this.word + "</p>";
        };

        Word.prototype.speak = function () {
            if (! this.wordsAloud) {
                console.log("Not speaking the word: " + this.word);
                return;
            }
            var utterance = new SpeechSynthesisUtterance(this.word);
            utterance.voice = this.voice;
            window.speechSynthesis.speak(utterance);
        };

        return Word;
    }());

    var MyWord = (function () {

        /**
         * Displays or reads a word I submitted.
         */

        var MyWord = function (options) {
            if (!(this instanceof MyWord)) {
                return new MyWord(options);
            }
            Word.call(this, options);
        };

        MyWord.prototype = Object.create(Word.prototype);

        MyWord.prototype.isIntendedForMe = function () {
            return true;
        };

        MyWord.prototype.print = function () {
            return "<p style='color: #1693A5;'>" + this.word + "</p>";
        };

        MyWord.prototype.speak = function () {
            console.log("Not speaking the word: " + this.word);
        };

        return MyWord;
    }());



    var WordFactory = (function () {

        /**
         * Creates the right kind of Word depending on who submitted it.
         */
        var WordFactory = function (options) {
            if (!(this instanceof WordFactory)) {
                return new WordFactory(options);
            }
            this.egoID = options.egoID;
            this.wordsAloud = options.wordsAloud;
        };

        WordFactory.prototype.create = function (message) {
            var settings = {
                message: message,
                egoID: this.egoID,
                wordsAloud: this.wordsAloud
            };
            if (message.author === this.egoID) {
                return MyWord(settings);
            }
            return Word(settings);
        };

        return WordFactory;
    }());

    var RecallDisplay = (function () {

        /**
         * Displays the list of unique recalled words.
         */
        var RecallDisplay = function (options) {
            if (!(this instanceof RecallDisplay)) {
                return new RecallDisplay(options);
            }
            this.wordFactory = options.wordFactory;
            this.socket = options.socket;
            this.$wordList = $("#recalled-words");
            this.socket.subscribe(this.updateWordList, "word_transmitted", this);
        };

        RecallDisplay.prototype.updateWordList = function (msg) {
            var smartWord = this.wordFactory.create(msg);

            if (smartWord.isIntendedForMe()) {
                uniqueWords.add(smartWord.word);
                this.$wordList.append(smartWord.print());
                smartWord.speak();
            }
        };

        return RecallDisplay;
    }());


    var WordSubmissionWithTurns = (function () {

        /**
         * Tracks turns and handles canditate word submissions.
         */
        var WordSubmissionWithTurns = function (options) {
            if (!(this instanceof WordSubmissionWithTurns)) {
                return new WordSubmissionWithTurns(options);
            }
            this.egoID = options.egoID;
            this.socket = options.socket;
            this._enabled = false;  // Disabled until turn info arrives
            this.$sendButton = $("#send-message");
            this.$passButton = $("#skip-turn");
            this.gameActions = [this.$sendButton, this.$passButton];
            this.$finishedButton = $("#leave-chat");
            this.$input = $("#reproduction");
            this._bindEvents();
            this.socket.subscribe(this.changeOfTurn, "change_of_turn", this);
        };

        WordSubmissionWithTurns.prototype.checkAndSendWord = function () {
            if (! this._enabled) {
                return;
            }
            var self = this;
            var newWord = uniqueWords.add(self.$input.val());
            if (! newWord) {
                return;
            }
            self.$input.val("");
            self.$input.focus();

            dallinger.createInfo(
                currentNodeId,
                {contents: newWord, info_type: "Info"}
            ).done(function () {
                var msg = {
                    type: "word_added",
                    word: newWord,
                    author: self.egoID
                };
                self.socket.send(msg);  // Report word submission to the backend
                self._enable();
            });
        };

        WordSubmissionWithTurns.prototype.skipTurn = function () {
            var msg = {
                type: "skip_turn",
            };
            this.socket.send(msg);
        };

        WordSubmissionWithTurns.prototype.changeOfTurn = function (msg) {
            currentPlayerId = msg.player_id;
            if (currentPlayerId === this.egoID) {
                this._enable();
            } else {
                this._disable();
            }
        };

        WordSubmissionWithTurns.prototype._bindEvents = function () {
            var self = this;
            $(document).keypress(function(e) {
                if (e.which === 13) {
                    self.$sendButton.click();
                    return false;
                }
            });
            self.$sendButton.click(function() {
                self.checkAndSendWord();
            });
            self.$passButton.click(function() {
                self.skipTurn();
            });
            self.$finishedButton.click(function () {
                self._disconnect();
                dallinger.allowExit();
                dallinger.goToPage("questionnaire");
            });
        };

        WordSubmissionWithTurns.prototype._disconnect = function () {
            var msg = {
                type: "disconnect",
                player_id: this.egoID,
                words: uniqueWords.retrieve()
            };
            this.socket.send(msg);
        };

        WordSubmissionWithTurns.prototype._disable = function () {
            this._enabled = false;
            this.gameActions.forEach(function (item) {
                item.attr("disabled", true);
            });
        };

        WordSubmissionWithTurns.prototype._enable = function () {
            this._enabled = true;
            this.gameActions.forEach(function (item) {
                item.attr("disabled", false);
            });
        };

        return WordSubmissionWithTurns;
    }());

    var WordSubmissionFreeForAll = (function () {

        /**
         * Tracks turns and handles canditate word submissions.
         */
        var WordSubmissionFreeForAll = function (options) {
            if (!(this instanceof WordSubmissionFreeForAll)) {
                return new WordSubmissionFreeForAll(options);
            }
            this.egoID = options.egoID;
            this.socket = options.socket;
            this._enabled = true;  // No waiting before you can type words
            this.$sendButton = $("#send-message");
            this.gameActions = [this.$sendButton];
            this.$finishedButton = $("#leave-chat");
            this.$input = $("#reproduction");
            this._bindEvents();
            this.socket.subscribe(this.changeOfTurn, "change_of_turn", this);
        };

        WordSubmissionFreeForAll.prototype = Object.create(WordSubmissionWithTurns.prototype);

        WordSubmissionFreeForAll.prototype._bindEvents = function () {
            var self = this;
            $(document).keypress(function(e) {
                if (e.which === 13) {
                    self.$sendButton.click();
                    return false;
                }
            });
            self.$sendButton.click(function() {
                self.checkAndSendWord();
            });
            self.$finishedButton.click(function () {
                self._disconnect();
                dallinger.allowExit();
                dallinger.goToPage("questionnaire");
            });
        };

        return WordSubmissionFreeForAll;
    }());


    $(document).ready(function() {

        var egoID = dallinger.getUrlParameter("participant_id"),
            socket = startSocket(egoID);

        new RecallDisplay({
            socket: socket,
            wordFactory: new WordFactory({egoID: egoID, wordsAloud: settings.wordsAloud})
        });
        new Timer({egoID: egoID, socket: socket});
        if (settings.enforceTurns) {
            new WordSubmissionWithTurns({egoID: egoID, socket: socket});
        } else {
            new WordSubmissionFreeForAll({egoID: egoID, socket: socket});
        }
        startPlayer();
    });

    function startSocket(playerID) {
        var socketSettings = {
            "endpoint": "chat",
            "broadcast": "memoryexpt3",
            "control": "memoryexpt3_ctrl",
        };
        var socket = pubsub.Socket(socketSettings);
        socket.open().done(
            function () {
                var data = {
                    type: "connect",
                    player_id: playerID
                };
                socket.send(data);
            }
        );
        return socket;
    }
    // Create the agent, then show the word list, then filler task
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
            $("#wordlist").html(wl.shift());
            setTimeout(
                function() {
                    showWordList(wl);
                },
                WORD_DISPLAY_DURATION_MSECS
            );
        }
    }

    function createQuestion(participantId, data) {
        return dallinger.post("/question/" + participantId, data);
    }

    function showFillerTask() {
        var participantId = dallinger.getUrlParameter("participant_id"),
            filler_answers = [];
        $("#stimulus").hide();
        $("#fillertask-form").show();

        setTimeout(
            function() {
                // store results of filler tasks in array
                $("#fillertask-form input").each(function( i, item ) {
                    filler_answers.push("{" + item.name + ": " + item.value + "}");
                });
                // stores all filler answers in the Question table
                createQuestion(
                    participantId,
                    {
                        question: "Fillerans",
                        response: filler_answers.join(", "),
                        number: 0
                    }
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
    }

}($, dallinger, pubsub, settings));
