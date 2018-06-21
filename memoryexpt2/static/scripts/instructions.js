/*global $, dallinger */

(function ($, dallinger) {

    $(document).ready(function() {
        // Proceed to the waiting room.
        $("#go-to-waiting-room").click(function() {
            dallinger.allowExit();
            dallinger.goToPage("waiting");
        });

    });

}($, dallinger));
