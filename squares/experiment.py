from dallinger.experiment import Experiment


class Squares(Experiment):
    """Define the structure of the experiment."""

    def __init__(self, session=None):
        """Call the same function in the super (see experiments.py in dallinger).

        The models module is imported here because it must be imported at
        runtime.

        A few properties are then overwritten.

        Finally, setup() is called.
        """
        super(Squares, self).__init__(session)
        self.experiment_repeats = 1
        self.initial_recruitment_size = 2
        if session:
            self.setup()

    def recruit(self):
        if not self.networks(full=False):
            self.recruiter.close_recruitment()

    def bonus(self, participant):
        """Give the participant a bonus for optimally completing grids"""

        # keep to two decimal points otherwise doesn't work
        return .10 #participant.bonus_earned
        # MONICA: this should be participant.bonus_earned from index.js, 
        # but I don't know how to do this so I'm just giving everyone
        # the full bonus right now.


    # hack for existing bug in 4.0.0
    def is_overrecruited(self, waiting_count):
        return False
