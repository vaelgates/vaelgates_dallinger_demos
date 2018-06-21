/*global $, dallinger, store */

(function ($, dallinger, store) {

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

    });
}($, dallinger, store));