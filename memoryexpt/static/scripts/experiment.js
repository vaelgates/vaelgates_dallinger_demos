var uniqueWords = [];
var currentNodeId;

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

    dallinger.allowExit();
    window.location.href = '/instructions';
  });

  // Do not consent to the experiment.
  $("#no-consent").click(function() {
    dallinger.allowExit();
    self.close();
  });

  // Proceed to the waiting room.
  $("#go-to-waiting-room").click(function() {
    dallinger.allowExit();
    window.location.href = '/waiting';
  });

  // Send a message.
  $("#send-message").click(function() {
    send_message();
  });

  // Leave the chatroom.
  $("#leave-chat").click(function() {
    leave_chatroom();
  });

});

// Create the agent.
create_agent = function() {
  var deferred = dallinger.createAgent();
  deferred.then(function (resp) {
    currentNodeId = resp.node.id;
    getWordList();
  }, function (err) {
    console.log(err);
    errorResponse = JSON.parse(err.response);
    if (errorResponse.hasOwnProperty("html")) {
      $("body").html(errorResponse.html);
    } else {
      dallinger.allowExit();
      dallinger.goToPage("questionnaire");
    }
  });
};


getWordList = function() {
  dallinger.get("/node/" + currentNodeId + "/received_infos").done(
    function(resp) {
      var wordList = JSON.parse(resp.infos[0].contents);
      showWordList(wordList);
    },
  );
};

showWordList = function(wl) {
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
      2000
    );
  }
};

showFillerTask = function() {
  $("#stimulus").hide();
  $("#fillertask-form").show();

  setTimeout(
    function() {
      showExperiment();
    },
    200//30000 MONICA
  );
};

showExperiment = function() {
  $("#fillertask-form").hide();
  $("#response-form").show();
  $("#send-message").removeClass("disabled");
  $("#send-message").html("Send");
  $("#reproduction").focus();
  get_transmissions();
};

get_transmissions = function() {
  dallinger.getTransmissions(
    currentNodeId,
    {status: "pending"}
  ).done(function(resp) {
    transmissions = resp.transmissions;
    for (var i = transmissions.length - 1; i >= 0; i--) {
      displayInfo(transmissions[i].info_id);
    }
    setTimeout(function () { get_transmissions(currentNodeId); }, 100);
  });
};

displayInfo = function(infoId) {
  dallinger.getInfo(currentNodeId, infoId).done(
    function(resp) {
      var word = resp.info.contents.toLowerCase();
      // if word hasn't appeared before, load into unique array and display
      if (uniqueWords.indexOf(word) === -1) {
        uniqueWords.push(word);
        $("#reply").append("<p>" + word + "</p>");
      }
    },
  );
};

send_message = function() {
  response = $("#reproduction").val();
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
    $(
      "#reply"
    ).append("<p style='color: #1693A5;'>" + response.toLowerCase() + "</p>"); //MONICA
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
};


leave_chatroom = function() {
  dallinger.allowExit();
  dallinger.goToPage("questionnaire");
};

$(document).keypress(function(e) {
  if (e.which === 13) {
    $("#send-message").click();
    return false;
  }
});
