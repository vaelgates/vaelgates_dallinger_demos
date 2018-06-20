/*global $, dallinger, store */

(function ($, dallinger, store) {

    var uniqueWords = [];
    var currentNodeId;
    // var FILLER_TASK_DURATION_MSECS = 30000
    // var WORD_DISPLAY_DURATION_MSECS = 2000
    // var FETCH_TRANSMISSION_FREQUENCY_MSECS = 100
    var FILLER_TASK_DURATION_MSECS = 3000;
    var WORD_DISPLAY_DURATION_MSECS = 1000;
    var FETCH_TRANSMISSION_FREQUENCY_MSECS = 100;
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
            send_message();
        });

        // Leave the chatroom.
        $("#leave-chat").click(function() {
            go.questionnaire();
        });

        if ($("body#experiment").length > 0) {
            console.log("OK to create agent.");
            create_agent();
        }
    });

    // Create the agent.
    function create_agent() {
        var deferred = dallinger.createAgent();
        deferred.then(function (resp) {
            currentNodeId = resp.node.id;
            getWordList();
        }, function (rejection) {
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
        get_transmissions();
    }

    function get_transmissions() {
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
                get_transmissions(currentNodeId);
            },
            FETCH_TRANSMISSION_FREQUENCY_MSECS);
        });
    }

    function displayInfo(infoId) {
        dallinger.getInfo(currentNodeId, infoId
        ).done(function(resp) {
            var word = resp.info.contents.toLowerCase();
            // if word hasn't appeared before, load into unique array and display
            if (uniqueWords.indexOf(word) === -1) {
                uniqueWords.push(word);
                $("#reply").append("<p>" + word + "</p>");
            }
        });
    }

    function send_message() {
        var response = $("#reproduction").val();
        // typing box
        // don't let people submit an empty response
        if (response.length === 0) {
            return;
        }

        // let people submit only if word doesn't have a space
        if (response.indexOf(" ") >= 0) {
            return;
        }

        // will not let you add a word that is non-unique
        if (uniqueWords.indexOf(response.toLowerCase()) === -1) {
            uniqueWords.push(response.toLowerCase());
            $("#reply").append("<p style='color: #1693A5;'>" + response.toLowerCase() + "</p>"); //MONICA
        } else {
            return; // don't let people submit if non-unique
        }

        $("#reproduction").val("");
        $("#reproduction").focus();

        dallinger.createInfo(
            currentNodeId,
            {contents: response, info_type: "Info"}
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