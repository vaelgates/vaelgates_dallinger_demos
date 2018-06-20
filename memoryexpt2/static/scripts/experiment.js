/*global $, dallinger, store */

(function ($, dallinger, store) {

    var currentNodeId;
    // var FILLER_TASK_DURATION_MSECS = 30000
    // var WORD_DISPLAY_DURATION_MSECS = 2000
    // var FETCH_TRANSMISSION_FREQUENCY_MSECS = 100
    var FILLER_TASK_DURATION_MSECS = 3000;
    var WORD_DISPLAY_DURATION_MSECS = 1000;
    var FETCH_TRANSMISSION_FREQUENCY_MSECS = 3000;
    var go = {
        leave: function () {
            dallinger.allowExit();
            self.close();
        },
        waitingRoom: function () {
            dallinger.allowExit();
            dallinger.goToPage("waiting");
        },
        instructions: function () {
            dallinger.allowExit();
            dallinger.goToPage("instructions");
        },
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

    $(document).ready(function() {
        // Print the consent form.
        $("#print-consent").click(function() {
            window.print();
        });

        // Consent to the experiment.
        $("#consent").click(function() {
            store.set("hit_id", dallinger.getUrlParameter("hit_id"));
            store.set("worker_id", dallinger.getUrlParameter("worker_id"));
            store.set("assignment_id", dallinger.getUrlParameter("assignment_id"));
            store.set("mode", dallinger.getUrlParameter("mode"));
            go.instructions();
        });

        // Do not consent to the experiment.
        $("#no-consent").click(function() {
            go.leave();
        });

        // Proceed to the waiting room.
        $("#go-to-waiting-room").click(function() {
            go.waitingRoom();
        });

        // Send a message.
        $("#send-message").click(function() {
            checkAndSendWord();
        });

        // Leave the chatroom.
        $("#leave-chat").click(function() {
            go.questionnaire();
        });

        if ($("#experiment").length > 0) {
            startPlayer();
        }
    });

    // Create the agent.
    function startPlayer() {
        dallinger.createAgent().done(function (resp) {
            currentNodeId = resp.node.id;
            getWordList();
        }).fail(function (rejection) {
            console.log(rejection);
            if (rejection.html) {
                $("body").html(rejection.html);
            } else {
                go.questionnaire();
            }
        });
    }


    function getWordList() {
        dallinger.get("/node/" + currentNodeId + "/received_infos").done(
            function(resp) {
                var wordList = JSON.parse(resp.infos[0].contents);
                showWordList(wordList);
            }
        );
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
                displayInfo(transmissions[i].info_id);
            }
            setTimeout(function () {
                getTransmissions(currentNodeId);
            },
            FETCH_TRANSMISSION_FREQUENCY_MSECS);
        });
    }

    function displayInfo(infoId) {
        dallinger.getInfo(
            currentNodeId, infoId
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

}($, dallinger, store));