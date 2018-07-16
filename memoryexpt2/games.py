import logging
import random
import time


logger = logging.getLogger(__name__)


class Turn(object):

    def __init__(self):
        self.start = time.time()
        self.timeout_secs = 5

    @property
    def is_expired(self):
        age = time.time() - self.start
        return age > self.timeout_secs


class ExpiredTurn(object):

    is_expired = True
    timeout_secs = 0

    def __init__(self):
        pass


class FixedRotation(object):
    """Rotate through players in a fixed order."""

    def __init__(self):
        self._player_ids = []
        self._active_player_idx = 0

    def add(self, player_id):
        if player_id not in self._player_ids:
            self._player_ids.append(player_id)

    def remove(self, player_id):
        if player_id in self._player_ids:
            self._player_ids.remove(player_id)

    def next(self):
        if not self.count:
            return
        self._active_player_idx = (self._active_player_idx + 1) % self.count
        return self.current

    @property
    def current(self):
        return self._player_ids[self._active_player_idx]

    @property
    def count(self):
        return len(self._player_ids)

    def __repr__(self):
        return "%s %r" % (self.__class__, self._player_ids)


class RandomRotation(FixedRotation):
    """Rotated through players in a random order, but don't repeat any
    players until every player has been visited.
    """
    def __init__(self):
        self._player_ids = []
        self._active_player = None
        self._had_a_turn = set()

    def next(self):
        all_players = set(self._player_ids)
        still_to_play = all_players - self._had_a_turn
        if not still_to_play:
            logger.info("Resetting round...")
            self._had_a_turn.clear()
            still_to_play = all_players
        if still_to_play:
            self._active_player = random.sample(still_to_play, 1)[0]
            self._had_a_turn.add(self._active_player)
        return self.current

    @property
    def current(self):
        return self._active_player


class TurnType(object):
    """Abstract base class"""

    is_ready = True

    def __init__(self, quorum):
        pass

    def add_player(self, player_id):
        pass

    def remove_player(self, player_id):
        pass

    def word_added(self):
        pass

    def turn_skipped(self):
        pass

    def tick(self):
        pass


class FreeFlowing(TurnType):
    """Any player can submit a (valid) word at any time"""
    nickname = u'free'
    enforce_turns = False

    def __init__(self, quorum):
        self.quorum = quorum
        self._players = []

    def add_player(self, player_id):
        self._players.append(player_id)
        logger.info("Player {} has connected.".format(player_id))
        logger.info(self._players)

    def remove_player(self, player_id):
        self._players.remove(player_id)
        logger.info('Player {} has disconnected.'.format(player_id))

    def word_added(self):
        pass

    def turn_skipped(self):
        pass

    @property
    def is_ready(self):
        return len(self._players) == self.quorum

    def tick(self):
        """We don't care"""
        pass


class FixedSequenceTurns(TurnType):

    nickname = u'fixed_turns'
    enforce_turns = True
    _rotation = FixedRotation

    def __init__(self, quorum):
        self.rotation = self._rotation()
        self.quorum = quorum
        self._turn = ExpiredTurn()

    def add_player(self, player_id):
        self.rotation.add(player_id)
        logger.info("Player {} has connected.".format(player_id))
        logger.info(self.rotation)

    def remove_player(self, player_id):
        was_players_turn = self.rotation.current == player_id
        self.rotation.remove(player_id)
        if was_players_turn:
            self.end_turn()
        logger.info('Player {} has disconnected.'.format(player_id))

    def word_added(self):
        self.end_turn()

    def turn_skipped(self):
        self.end_turn()

    def end_turn(self):
        self._turn = ExpiredTurn()

    def new_turn(self):
        self._turn = Turn()

    @property
    def turn_is_over(self):
        return self._turn.is_expired

    @property
    def all_players_have_joined(self):
        return self.rotation.count == self.quorum

    @property
    def is_ready(self):
        return self.all_players_have_joined

    def tick(self):
        """Update play state and return any messages to be published"""
        if self.turn_is_over:
            self.new_turn()
            return self.change_player()

    def change_player(self):
        next_player = self.rotation.next()
        message = {
            'type': 'change_of_turn',
            'player_id': next_player,
            'turn_seconds': self._turn.timeout_secs
        }
        return message


class RandomSequenceTurns(FixedSequenceTurns):

    nickname = u'random_turns'
    _rotation = RandomRotation


def _descendent_classes(cls):
    for cls in cls.__subclasses__():
        yield cls
        for cls in _descendent_classes(cls):
            yield cls


BY_NAME = {}
for cls in _descendent_classes(TurnType):
    BY_NAME[cls.__name__] = BY_NAME[cls.nickname] = cls


def by_name(name, quorum):
    """Attempt to return a game class by name.

    Actual class names and known nicknames are both supported.
    """
    klass = BY_NAME.get(name)
    if klass is not None:
        return klass(quorum)
