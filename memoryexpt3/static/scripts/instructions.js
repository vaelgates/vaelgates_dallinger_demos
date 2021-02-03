/*global $, dallinger */

(function ($, dallinger) {

    var TEST_PHRASE = "The cat jumps over the box";
    var ZOOM_CODE = "zoomcode"

    $(document).ready(function() {
      // Proceed to the instructions_1.
        $("#go-to-instructions_1").click(function() {
            dallinger.allowExit();
            dallinger.goToPage("instructions_1");
        });

        // Proceed to instructions_2
        $("#go-to-instructions_2").click(function() {
            dallinger.allowExit();
            dallinger.goToPage("instructions_2");
        });

        // Proceed to the waiting room.
        $("#go-to-waiting-room").click(function() {
            dallinger.allowExit();
            dallinger.goToPage("waiting");
        });

        $('#test-sound').click(function () {
            var utterance = new SpeechSynthesisUtterance(TEST_PHRASE);
            var voice = speechSynthesis.getVoices().filter(
                function (voice) { return voice.name === "Alex"; }
            )[0];
            utterance.voice = voice;
            window.speechSynthesis.speak(utterance);
        });

        $('#compare-phrases').click(function () {
            var heardAs = $('#heard-as').val();
            score = similarity(TEST_PHRASE, heardAs);
            if (score >= 0.75) {
                result = '<div class="alert alert-success" role="alert">Everything seems to work. You can go ahead with the experiment.</div>';
                $("#go-to-instructions_1")[0].disabled = false;
            } else {

                result = '<div class="alert alert-danger role="alert">Either sound does not work, or quality was too bad to understand the phrase. Please fix your sound to continue.</div>';
            }
            $('#sound-test-result').html(result);
        });

        // Open Zoom link
        $("#open-zoom-link").click(function() {
            window.open('https://berkeley.zoom.us/j/98488654288')
        });

        $('#compare-zoom-code').click(function () {
            var seenZoomCode = $('#seen-zoom-code').val();
            score = similarity(ZOOM_CODE, seenZoomCode);
            if (score >= 0.90) {
                result = '<div class="alert alert-success" role="alert">Everything seems to work. You can go ahead with the experiment.</div>';
                $("#go-to-instructions_2")[0].disabled = false;
            } else {

                result = '<div class="alert alert-danger role="alert">Error. Please try again.</div>';
            }
            $('#zoom-code-result').html(result);
        });

    });

    function similarity(s1, s2) {
        var longer = s1;
        var shorter = s2;
        if (s1.length < s2.length) {
      	longer = s2;
	      shorter = s1;
        }
        var longerLength = longer.length;
        if (longerLength == 0) {
	      return 1.0;
        }
        return (longerLength - editDistance(longer, shorter)) / parseFloat(longerLength);
    }

    function editDistance(s1, s2) {
        s1 = s1.toLowerCase();
        s2 = s2.toLowerCase();

        var costs = new Array();
        for (var i = 0; i <= s1.length; i++) {
            var lastValue = i;
            for (var j = 0; j <= s2.length; j++) {
              if (i == 0)
                  costs[j] = j;
              else {
                  if (j > 0) {
                    var newValue = costs[j - 1];
                    if (s1.charAt(i - 1) != s2.charAt(j - 1))
                        newValue = Math.min(Math.min(newValue, lastValue),
                          costs[j]) + 1;
                    costs[j - 1] = lastValue;
                    lastValue = newValue;
                  }
              }
            }
            if (i > 0)
              costs[s2.length] = lastValue;
        }
        return costs[s2.length];
    }

}($, dallinger));
