import datetime
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
from . import games


logger = logging.getLogger(__file__)

extra_routes = flask.Blueprint(
    'extra_routes',
    __name__,
    template_folder='templates',
    static_folder='static')


@extra_routes.route("/exp")
def serve_game():
    """Render the game as a Flask template, so we can include
    interpolated values from the Experiment.
    """
    return flask.render_template("exp.html")


class CoordinationChatroom(dlgr.experiments.Experiment):
    """Define the structure of the experiment."""

    channel = 'memoryexpt2_ctrl'

    def __init__(self, session):
        """Initialize the experiment."""
        super(CoordinationChatroom, self).__init__(session)
        self.experiment_repeats = 1
        self.num_participants = 2 #55 #55 #140 below
        self.initial_recruitment_size = 2 #self.num_participants * 1 #note: can't do *2.5 here, won't run even if the end result is an integer
        self.quorum = self.num_participants  # quorum is read by waiting room
        self.game = games.by_name(u'free', quorum=self.quorum)
        self.enforce_turns = self.game.enforce_turns  # Configures front-end
        import models
        self.models = models
        self.known_classes["Fillerans"] = models.Fillerans
        if session:
            self.setup()

    @property
    def background_tasks(self):
        return [
            self.game_loop,
        ]

    def record_waiting_room_exit(self, player_id):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        end_waiting_room = datetime.datetime.now().strftime(DATETIME_FORMAT)
        participant = self.session.query(dlgr.models.Participant)
        participant.property1 = end_waiting_room
        self.session.commit()
        logger.info("Player {} waiting room exit: {}.".format(player_id,
                                                              end_waiting_room))

    def handle_connect(self, msg):
        player_id = msg['player_id']
        self.record_waiting_room_exit(player_id)
        self.game.add_player(player_id)

    def handle_disconnect(self, msg):
        self.game.remove_player(msg['player_id'])

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

    @property
    def topology(self):
        from . import topologies
        # return topologies.Baby4()
        return topologies.Collaborative()

    def create_network(self):
        """Create a new network by reading the configuration file."""
        logger.info("Using the {} network".format(self.topology))
        return self.topology.network(max_size=self.num_participants + 1)  # add a Source

    def bonus(self, participant):
        """Give the participant a bonus for waiting."""

        DOLLARS_PER_HOUR = 5.0
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        try:
            end_waiting_room = datetime.datetime.strptime(participant.property1,
                                                          DATETIME_FORMAT)
        except ValueError:
            # just in case something went wrong saving wait room end time
            end_waiting_room = participant.end_time
        t = end_waiting_room - participant.creation_time

        # keep to two decimal points otherwise doesn't work
        return round((t.total_seconds() / 3600) * DOLLARS_PER_HOUR, 2)

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
        self._transmit_to_neighbors(node, info)
        # self._transmit_to_random_neighbor(node, info)

    def _transmit_to_neighbors(self, node, info):
        recipients = [node.participant_id]
        for agent in node.neighbors():
            node.transmit(what=info, to_whom=agent)
            recipients.append(agent.participant_id)

        self.report_word_transmitted(
            word=info.contents,
            recipients=recipients,
            author=node.participant_id
        )

    def _transmit_to_random_neighbor(self, node, info):
        """Transfer info to only one neighbor."""
        agent = random.choice(node.neighbors())
        node.transmit(what=info, to_whom=agent)
        recipients = [node.participant_id, agent.participant_id]
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
            expt_wordlist = random.sample(wordlist, 5) #MONICA

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

