import logging
import six
from datetime import datetime


logger = logging.getLogger(__name__)
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class Bonus(object):
    """Calculate bonuses for a participant.
    """

    dollars_per_hour_for_waiting = 7.0
    dollars_per_word = .015 #.005

    def __init__(self, participant):
        self.participant = participant

    @property
    def wait_time(self):
        """How many seconds did the participant sit in the waiting room?
        """
        try:
            end_waiting_room = datetime.strptime(
                self.participant.property1, DATETIME_FORMAT
            )
        except (TypeError, ValueError):
            # just in case something went wrong saving wait room end time
            logger.info("Falling back to participant end time!")
            end_waiting_room = self.participant.end_time

        t = end_waiting_room - self.participant.creation_time

        return t.total_seconds()

    @property
    def word_count(self):
        if self.participant.property2:
            return int(self.participant.property2)

        return 0

    @property
    def for_waiting(self):
        """Bonus based on how long the participant sat in the waiting room.
        """
        # Cap the bonus for waiting time at 15min (=.25 hours)
        return min((self.wait_time / 3600) * self.dollars_per_hour_for_waiting,
                   0.25 * self.dollars_per_hour_for_waiting)

    @property
    def for_words(self):
        """Bonus based on the number of words credited to the participant

        They may not have submitted them themselves, depending on the game
        configuration.
        """
        return self.word_count * self.dollars_per_word

    @property
    def total(self):
        """Total of all bonus types"""
        return self.for_waiting + self.for_words

    def record_wait_time(self):
        end_waiting_room = datetime.now().strftime(DATETIME_FORMAT)
        self.participant.property1 = end_waiting_room

    def record_word_list(self, words):
        self.participant.property2 = six.text_type(len(words))

    def __repr__(self):
        return "%s (participant: %s, wait: %s, words: %s)" % (
            self.__class__.__name__,
            self.participant,
            self.wait_time,
            self.word_count
        )
