var my_node_id;

// Consent to the experiment.
$(document).ready(function() {

  // do not allow user to close or reload
  dallinger.preventExit = true;

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
    window.location.href = '/instructions-1';
  });

  // Consent to the experiment.
  $("#no-consent").click(function() {
    dallinger.allowExit();
    window.close();
  });


  // Go-to-experiment button-- only proceed if you get all questions correct
  $("#go-to-experiment").click(function() {
    paradigmQ = $("#paradigmQ").val()
    knowgoalQ = $("#knowgoalQ").val()
    diffpartnerQ = $("#diffpartnerQ").val()
    if (paradigmQ == 1) {
      if (knowgoalQ == 1){ 
        if (diffpartnerQ == 1){
          dallinger.allowExit();
          dallinger.goToPage('exp');
        }
      }
    }
  });

  // Finish game
  $("#alldone").click(function() {
    $("#alldone").addClass('disabled');
    $("#alldone").html('Sending...');
    dallinger.allowExit();
    dallinger.goToPage('questionnaire');
  });

});

// Create the agent.
var create_agent = function() {
  dallinger.createAgent()
    .done(function (resp) {
      my_node_id = resp.node.id;
      get_info();
    })
    .fail(function () {
      dallinger.allowExit();
      dallinger.goToPage('questionnaire');
    });
};

var get_info = function() {
  dallinger.getReceivedInfos(my_node_id)
    .done(function (resp) {
    })
    .fail(function (err) {
      console.log(err);
      var errorResponse = JSON.parse(err.response);
      $('body').html(errorResponse.html);
    });
};
