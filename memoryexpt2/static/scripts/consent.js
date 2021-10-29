/*global $, dallinger */

(function ($, dallinger) {

    var go = {
        leave: function () {
            dallinger.allowExit();
            self.close();
        },
        instructions: function () {
            dallinger.allowExit();
            dallinger.goToPage("instructions");
        },
    };

    $(document).ready(function() {
        // Print the consent form.
        $("#print-consent").click(function() {
            window.print();
        });

        // Consent to the experiment.
        $("#consent").click(function() {
            go.instructions();
        });

        // Do not consent to the experiment.
        $("#no-consent").click(function() {
            go.leave();
        });

    });
}($, dallinger));