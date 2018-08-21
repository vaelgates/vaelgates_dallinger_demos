import flask
import gevent
import json
import logging
import random
import six

import dallinger as dlgr
from dallinger.heroku.worker import conn as redis
from dallinger.models import Node
from dallinger.nodes import Source
from . import bonuses
from . import games
from . import topologies
from . import transmission
from . import models


logger = logging.getLogger(__file__)

extra_routes = flask.Blueprint(
    'extra_routes',
    __name__,
    template_folder='templates',
    static_folder='static')


@extra_routes.route("/experiment")
def serve_game():
    """Render the game as a Flask template, so we can include
    interpolated values from the Experiment.
    """
    return flask.render_template("experiment.html")


@extra_routes.route("/instructions")
def serve_instructions():
    """Render the instructions as a Flask template, so we can include
    interpolated values from the Experiment.
    """
    return flask.render_template("instructions.html")


def extra_parameters():
    config = dlgr.config.get_config()
    config.register('mexp_topology', six.text_type, [], False)
    config.register('mexp_turn_type', six.text_type, [], False)
    config.register('mexp_transmission_mode', six.text_type, [], False)
    config.register('mexp_words_aloud', bool, [], False)


class CoordinationChatroom(dlgr.experiments.Experiment):
    """Define the structure of the experiment."""

    channel = 'memoryexpt2_ctrl'

    def __init__(self, session):
        """Initialize the experiment."""
        super(CoordinationChatroom, self).__init__(session)
        config = dlgr.config.get_config()
        self.experiment_repeats = 1
        self.num_participants = 2 #55 #55 #140 below
        self.initial_recruitment_size = self.num_participants * 1 #note: can't do *2.5 here, won't run even if the end result is an integer
        self.quorum = self.num_participants  # quorum is read by waiting room
        self.words_aloud = config.get(u'mexp_words_aloud', False)
        self.topology = topologies.by_name(
            config.get(u'mexp_topology', u'collaborative')
        )
        self.game = games.by_name(
            config.get(u'mexp_turn_type', u'fixed_turns'), quorum=self.quorum
        )
        self.transmitter = transmission.by_name(
            config.get(u'mexp_transmission_mode', u'promiscuous')
        )
        logger.info('Using "{}" turns with "{}" transmitter.'.format(
            self.game.nickname, self.transmitter.nickname
        ))
        self.enforce_turns = self.game.enforce_turns  # Configures front-end
        self.models = models
        self.known_classes["Fillerans"] = models.Fillerans
        if session:
            self.setup()

    @property
    def background_tasks(self):
        return [
            self.game_loop,
        ]

    def get_participant(self, player_id):
        return self.session.query(dlgr.models.Participant).get(player_id)

    def record_waiting_room_exit(self, player_id):
        bonus = bonuses.Bonus(self.get_participant(player_id))
        bonus.record_wait_time()
        logger.info(
            "Player {} left waiting room after {} seconds.".format(
                player_id,
                bonus.wait_time
            )
        )
        self.session.commit()

    def record_word_list(self, player_id, words):
        player_words = set(words)
        valid_words = self.retrieve_valid_words()
        player_valid_words = valid_words.intersection(player_words)

        # participants are paid based on the number of words they got correct
        bonus = bonuses.Bonus(self.get_participant(player_id))
        bonus.record_word_list(player_valid_words)
        self.session.commit()

    def retrieve_valid_words(self):
        node = Node.query.filter_by(type='free_recall_list_source').one()
        # Could we just do: json.loads(node.infos()[0].contents) ?
        wordlist = []
        for i in node.infos():
            if i.contents is not None:
                # json.dumps() on the way in, so json.loads() on the way out:
                wordlist = json.loads(i.contents)
                break
        return set(wordlist)

    def handle_connect(self, msg):
        player_id = msg['player_id']
        self.record_waiting_room_exit(player_id)
        self.game.add_player(player_id)

    def handle_disconnect(self, msg):
        self.game.remove_player(msg['player_id'])
        self.record_word_list(msg['player_id'], msg['words'])

    def handle_word_added(self, msg):
        self.game.word_added()

    def handle_skip_turn(self, msg):
        self.game.turn_skipped()

    def game_loop(self):
        """Track turns and send current player and turn length to clients."""
        gevent.sleep(1.00)
        while not self.game.is_ready:
            gevent.sleep(0.1)
        while True:
            gevent.sleep(0.1)
            msg = self.game.tick()
            if msg:
                self.publish(msg)

    def publish(self, msg):
        """Publish a message to all memoryexpt2 clients"""
        redis.publish('memoryexpt2', json.dumps(msg))

    def send(self, raw_message):
        """Socket interface; point of entry for incoming messages.

        param raw_message is a string with a channel prefix, for example:

            'memoryexpt2_ctrl:{"type":"connect","player_id":1}'
        """
        mapping = {
            'connect': self.handle_connect,
            'disconnect': self.handle_disconnect,
            'word_added': self.handle_word_added,
            'skip_turn': self.handle_skip_turn,
        }
        if raw_message.startswith(self.channel + ":"):
            logger.info("We received a message for our channel: {}".format(
                raw_message))
            body = raw_message.replace(self.channel + ":", "")
            msg = json.loads(body)
            if msg['type'] in mapping:
                mapping[msg['type']](msg)
        else:
            logger.info("Received a message, but not our channel: {}".format(
                raw_message))

    def is_a_legal_word(self, word):
        # Our words contain no spaces, so if we've got a space, it's probably
        # the "Filler Task" submission.
        return ' ' not in word

    def report_word_transmitted(self, word, recipients, author):
        """A word was submitted and transmitted to connected players. Publish
        this info to clients so they can add the word to their own word list
        if appropriate.

        'author's (participant IDs) are really strings, not integers, so we
        do the conversion here.
        """
        if not self.is_a_legal_word(word):
            return

        message = {
            'type': 'word_transmitted',
            'word': word,
            'author': six.text_type(author),
            'recipients': json.dumps([six.text_type(r) for r in recipients])
        }
        logger.info('Sending word transmission: "{}"'.format(message))
        self.publish(message)

    def setup(self):
        """Setup the networks.

        Setup only does stuff if there are no networks, this is so it only
        runs once at the start of the experiment. It first calls the same
        function in the super (see experiments.py in dallinger). Then it adds a
        source to each network.
        """
        if not self.networks():
            super(CoordinationChatroom, self).setup()
            for net in self.networks():
                FreeRecallListSource(network=net)

    def create_network(self):
        """Create a new network by reading the configuration file."""
        logger.info("Using the {} network".format(self.topology))
        return self.topology.network(max_size=self.num_participants + 1)  # add a Source

    def bonus(self, participant):
        """Return a total bonus for a participant.
        """
        bonus = bonuses.Bonus(participant)
        logger.info("For waiting: ${:.2f}, for words: ${:.2f}".format(
            bonus.for_waiting, bonus.for_words)
         )
        # keep to two decimal points otherwise doesn't work
        return round(bonus.total, 2)

    def add_node_to_network(self, node, network):
        """Add node to the chain and receive transmissions."""
        network.add_node(node)
        source = network.nodes(type=Source)[0]  # find the source in the network
        source.connect(direction="to", whom=node)  # link up the source to the new node
        source.transmit(to_whom=node)  # in networks.py code, transmit info to the new node
        node.receive()  # new node receives everything

        # walk through edges
        for edge in self.topology.edges():
            try:
                node0 = Node.query.filter_by(participant_id=edge[0]+1).one()
                node1 = Node.query.filter_by(participant_id=edge[1]+1).one()
                node0.connect(direction="from", whom=node1)  # connect backward
                node1.connect(direction="from", whom=node0)  # connect forward

            except Exception:
                pass

    def info_post_request(self, node, info):
        """Run when a request to create an info is complete."""
        recipients = self.transmitter.transmit(node, info)
        self.report_word_transmitted(
            word=info.contents,
            recipients=recipients,
            author=node.participant_id
        )

    def create_node(self, participant, network):
        """Create a node for a participant."""
        return dlgr.nodes.Agent(network=network, participant=participant)


class FreeRecallListSource(Source):
    """A Source that reads in a random list from a file and transmits it."""

    __mapper_args__ = {
        "polymorphic_identity": "free_recall_list_source"
    }

    def _contents(self):
        """Define the contents of new Infos.
        transmit() -> _what() -> create_information() -> _contents().
        """

        #CODE FOR INDIVIDUAL EXPTS
        #(samples 60 words from the big wordlist for each participant)
        # wordlist = "groupwordlist.md"
        # with open("static/stimuli/{}".format(wordlist), "r") as f:
        #    wordlist = f.read().splitlines()
        #    return json.dumps(random.sample(wordlist,60))



        # CODE FOR GROUP EXPTS
        # (has one word list for the experiment
        # (draw 60 words from "groupwordlist.md") then
        # reshuffles the words within each participant

        ### read in UUID
        exptfilename = "experiment_id.txt"
        exptfile = open(exptfilename, "r")
        UUID = exptfile.read()  # get UUID of the experiment

        wordlist = "groupwordlist.md"
        with open("static/stimuli/{}".format(wordlist), "r") as f:

            ### get a wordlist for the expt
            # reads in the file with a big list of words
            wordlist = f.read().splitlines()
            # use the UUID (unique to each expt) as a seed for
            # the pseudorandom number generator.
            # the random sample will be the same for everyone within an
            # experiment but different across experiments b/c
            # they have different UUIDs.
            random.seed(UUID)
            # sample 60 words from large word list without replacement
            expt_wordlist = random.sample(wordlist, 60) #5 for testing

            ### shuffle wordlist for each participant
            random.seed()  # an actually random seed
            random.shuffle(expt_wordlist)
            return json.dumps(expt_wordlist)

        # OLD:
        # shuffles all words
        #wordlist = "60words.md"
        #with open("static/stimuli/{}".format(wordlist), "r") as f:
        #    wordlist = f.read().splitlines()
        #    return json.dumps(random.sample(wordlist,60))
        ##    random.shuffle(wordlist)
        ##    return json.dumps(wordlist)

