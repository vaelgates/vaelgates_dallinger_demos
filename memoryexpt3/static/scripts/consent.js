/*global $, dallinger */

(function ($, dallinger) {

    var go = {
        leave: function () {
            dallinger.allowExit();
            self.close();
        },
        instructions_0: function () {
            dallinger.allowExit();
            dallinger.goToPage("instructions_0");
        },
    };

    $(document).ready(function() {
        // Print the consent form.
        $("#print-consent").click(function() {
            window.print();
        });

        // Consent to the experiment.
        $("#consent").click(function() {
            go.instructions_0();
        });

        // Do not consent to the experiment.
        $("#no-consent").click(function() {
            go.leave();
        });

    });
}($, dallinger));