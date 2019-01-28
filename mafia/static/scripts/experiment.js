/* global $, dallinger */
var currentNodeId;
var currentNodeName;
var currentNodeType;
var wasDaytime = 'False';
var switches = 0;
var voted = false;

$(document).ready(function() {
  // Do not print the consent form.
  $("#print-consent").click(function() {
    window.print();
  });

  // Send a message.
  $("#send-message").click(function() {
    send_message();
  });

  // Vote.
  $("#vote").click(function() {
    vote();
  });

  // Leave the chatroom.
  $("#leave-chat").click(function() {
    leave_chatroom();
  });

});

// Create the agent.
var create_agent = function() {
  var deferred = dallinger.createAgent();
  deferred.then(function (resp) {
    currentNodeId = resp.node.id;
    currentNodeName = resp.node.property1;
    currentNodeType = resp.node.type;
    $("#narrator").html("The game will begin shortly...");
    $("#stimulus").show();
    // this is how long the "The game will begin shortly..." message gets displayed (ms)
    setTimeout(function () { $("#stimulus").hide(); showExperiment(); }, 2000);
    // if you change this number you have to change it in "start_duration" in experiment.py
  }, function (err) {
    console.log(err);
    var errorResponse = JSON.parse(err.response);
    if (errorResponse.hasOwnProperty("html")) {
      $("body").html(errorResponse.html);
    } else {
      dallinger.allowExit();
      dallinger.goToPage("questionnaire");
    }
  });
};

var getParticipants = function() {
  dallinger.get("/live_participants/" + currentNodeId + '/' + 1).done(
    function (resp) {
      var participantList = resp.participants;
      showParticipants(participantList, "#participants", 'option');
    }
  );
};

var getMafia = function() {
  dallinger.get("/live_participants/" + currentNodeId + '/' + 0).done(
    function (resp) {
      var mafiaList = resp.participants;
      showParticipants(mafiaList, "#mafiosi", 'li');
    }
  );
};

var showParticipants = function(participantList, tag, subtag) {

  var i;
  $(tag).html('');
  if (tag == "#mafiosi") {
    $(tag).append('<h4>List of Living Mafia</h4>');
  }
  for (i = 0; i < participantList.length; i++) {
    // Add the next participant.
    var name = participantList[i];
    if (tag == "#mafiosi"){
      $(tag).append('<' + subtag + '>' + name + '</' + subtag + '>');
    }
    if (tag == "#participants") {
      // don't allow participants to see / vote on themselves
      if (name.indexOf("(you!)") == -1) {
        $(tag).append('<' + subtag + '>' + name + '</' + subtag + '>');
      }
    }
  }
};

var showExperiment = function() {
  getParticipants();
  $('#name').html('You are a ' + currentNodeType + "! Your player's name is: " + currentNodeName);
  $("#player").show();
  $("#clock").show();
  $("#response-form").show();
  $("#send-message").removeClass("disabled");
  $("#send-message").html("Send");
  $("#reproduction").focus();
  $("#vote-form").show();
  if (currentNodeType == 'mafioso') {
    getMafia();
    $("#mafia").show();
    $("#note").show();
    $("#vote-note").show();
  } else {
    $("#note").html('You cannot send messages at night!');
    $("#note").show();
  }
  get_transmissions();
};

var check_phase = function() {
  var deferred = dallinger.get(
    "/phase/" + currentNodeId + '/' + switches + '/' + wasDaytime
  );
  deferred.then(function (resp) {
    // end game if there's a winner
    if (resp.winner) {
      $("#player").hide();
      $("#clock").hide();
      $("#response-form").hide();
      $("#vote-form").hide();
      if (currentNodeType == 'mafioso') {
        $("#mafia").hide();
        $("#note").hide();
        $("#vote-note").hide();
      }
      $("#narrator").html(resp.victim_name + ", who is a " + resp.victim_type + ", has been eliminated! The " + resp.winner + " have won!");
      $("#stimulus").show();
      setTimeout(function () { leave_chatroom(); }, 8000);
    // otherwise...
    } else {
      if (resp.daytime == 'True') {
        $('#remaining').html('Time remaining this day: ' + resp.time);
      } else {
        $('#remaining').html('Time remaining this night: ' + resp.time);
      }

      if (wasDaytime != resp.daytime) {
        wasDaytime = resp.daytime;
        switches++;
        voted = false;
        $("#reply").append("<hr>");
        $("#votes").append("<hr>");
        if (resp.daytime == 'False') { // Nighttime
          $("#reply").append("<h5>Night " + ((switches / 2) + 1).toString() + "</h5>");
          $("#votes").append("<h5>Night " + ((switches / 2) + 1).toString() + "</h5>");
          document.body.style.backgroundColor = "royalblue";
          if (resp.victim_name) {
            $("#narrator").html(resp.victim_name + ", who is a " + resp.victim_type + ", has been eliminated!");
          } else {
            $("#narrator").html("No one has been eliminated this round!");
          }
          if (currentNodeType == 'mafioso') {
            $("#note").html('These messages are private!');
            $("#vote-note").html('These votes are private!');
          } else {
            $("#note").show();
          }

        } else { // Daytime
          $("#reply").append("<h5>Day " + ((switches + 1) / 2).toString() + "</h5>");
          $("#votes").append("<h5>Day " + ((switches + 1) / 2).toString() + "</h5>");
          document.body.style.backgroundColor = "lightskyblue";
          if (resp.victim_name) {
            $("#narrator").html(resp.victim_name + " has been eliminated!");
          } else {
            $("#narrator").html("No one has been eliminated this round!");
          }
          if (currentNodeType == 'mafioso') {
            $("#note").html('These messages are public!');
            $("#vote-note").html('These votes are public!');
          } else {
            $("#note").hide();
          }
        }
        // Any time...
        $("#stimulus").show();
        if (resp.victim_name == currentNodeName) {
          // this is how long the "this person has been eliminated!" message gets displayed (ms)
          setTimeout(function () { leave_chatroom(); }, 10000);
          // if you change this number below you should change it here for consistency
        }
        getParticipants();
        if (currentNodeType == 'mafioso' && resp.victim_type == 'mafioso') {
          getMafia();
        }
        // this is how long the "this person has been eliminated!" message gets displayed (ms)
        setTimeout(
          function () { $("#stimulus").hide(); get_transmissions(currentNodeId); },
          10000
        );
      // if you change this number you have to change it in "break_duration" in experiment.py
      } else if (resp.time > 0 && resp.time <= 10 && voted == false && (resp.daytime == 'True' || (resp.daytime == 'False' && currentNodeType == 'mafioso'))) {
        if (resp.time == 1) {
          $("#narrator").html("You have " + resp.time + " second remaining to vote. Please vote now!");
        } else {
          $("#narrator").html("You have " + resp.time + " seconds remaining to vote. Please vote now!");
        }
        $("#stimulus").show();
        setTimeout(function () { get_transmissions(currentNodeId); }, 100);
      } else {
        setTimeout(function () { $("#stimulus").hide(); get_transmissions(currentNodeId); }, 100);
      }
    }
  }, function (err) {
    setTimeout(function () { get_transmissions(currentNodeId); }, 100);
  });
};

var get_transmissions = function() {
  dallinger.getTransmissions(
    currentNodeId,
    {status: "pending"}
  ).done(function(resp) {
    var transmissions = resp.transmissions;
    for (var i = transmissions.length - 1; i >= 0; i--) {
      displayInfo(transmissions[i].info_id);
    }
    check_phase();
  });
};

var displayInfo = function(infoId) {
  dallinger.getInfo(currentNodeId, infoId).done(
    function(resp) {
      var word = resp.info.contents;
      if (resp.info.type === 'text') {
        $("#reply").append("<p>" + word + "</p>");
      } else {
        $("#votes").append("<p>" + word + "</p>");
      }
    }
  );
};

var send_message = function() {
  if (currentNodeType === 'bystander' && wasDaytime === 'False') {
    return;
  }
  var response = $("#reproduction").val();
  // typing box
  // don't let people submit an empty response
  if (response.length === 0) {
    return;
  }
  response = currentNodeName + ': ' + $("#reproduction").val();

  $(
    "#reply"
  ).append("<p style='color: #853d0a;'>" + response + "</p>");

  $("#reproduction").val("");
  $("#reproduction").focus();

  dallinger.createInfo(
    currentNodeId,
    {contents: response, info_type: "Text"}
  ).done(function(resp) {
    $("#send-message").removeClass("disabled");
    $("#send-message").html("Send");
  });
};

var allowedToVoteNow = function(nodeType, isDaytime, hasVotedAlready) {
  if (nodeType === 'bystander' && ! isDaytime) {
    console.log("Bystanders can't vote during the nighttime");
    return false;
  }

  if (hasVotedAlready) {
    console.log("You voted already!");
    return false;
  }
  return true;

};

var vote = function() {
  var isDaytime = wasDaytime !== 'False';
  if (! allowedToVoteNow(currentNodeType, isDaytime, voted)) {
    return;
  }
  voted = true;
  var response = currentNodeName + ': ' + $("#participants").val();
  $(
    "#votes"
  ).append("<p style='color: #853d0a;'>" + response + "</p>");

  dallinger.createInfo(
    currentNodeId,
    {contents: response, info_type: "Vote"}
  ).done(function (resp) {
    $("#vote").removeClass("disabled");
    $("#vote").html("Vote (not changeable!)");
  });
};

var leave_chatroom = function() {
  dallinger.allowExit();
  dallinger.goToPage("questionnaire");
};

$(document).keypress(function(e) {
  if (e.which === 13) {
    $("#send-message").click();
    return false;
  }
});
