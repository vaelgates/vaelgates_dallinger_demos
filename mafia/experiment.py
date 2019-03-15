"""Mafia game."""

import json
import random

import dallinger as dlgr
from dallinger import db
from dallinger.models import Node, Info, Participant, Network, timenow
from dallinger.nodes import Source
from datetime import datetime
from flask import Blueprint, Response
from faker import Faker
fake = Faker()


DOLLARS_PER_HOUR = 5.0
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class MafiaExperiment(dlgr.experiments.Experiment):
    """Define the structure of the experiment."""

    def __init__(self, session):
        """Initialize the experiment."""
        super(MafiaExperiment, self).__init__(session)
        import models
        self.models = models
        self.skip_instructions = True  # If true, you'll go directly to /waiting
        self.experiment_repeats = 1
        self.num_participants = 4
        self.num_mafia = 1
        # Note: can't do * 2.5 here, won't run even if the end result is an integer
        self.initial_recruitment_size = self.num_participants
        self.quorum = self.num_participants
        if session:
            self.setup()
        self.known_classes["Text"] = models.Text
        self.known_classes["Vote"] = models.Vote

    def setup(self):
        """Setup the networks.

        Setup only does stuff if there are no networks, this is so it only
        runs once at the start of the experiment. It first calls the same
        function in the super (see experiments.py in dallinger). Then it adds a
        source to each network.
        """
        if not self.networks():
            super(MafiaExperiment, self).setup()
            for net in self.networks():
                Source(network=net)

    def create_network(self):
        """Create a new network by reading the configuration file."""

        mafia_network = self.models.MafiaNetwork(
            max_size=self.num_participants + 1
        )  # add a Source
        mafia_network.daytime = 'False'
        mafia_network.winner = None
        mafia_network.last_victim_name = None
        return mafia_network

    def record_waiting_room_exit(self, player_id):
        # Nothing calling this currently.
        end_waiting_room = datetime.now().strftime(DATETIME_FORMAT)
        self.participant.property1 = end_waiting_room

    def bonus(self, participant):
        """Give the participant a bonus for waiting."""
        try:
            end_waiting_room = datetime.strptime(participant.property1,
                                                 DATETIME_FORMAT)
        except (TypeError, ValueError):
            # just in case something went wrong saving wait room end time
            last_participant_creation_time = Participant.query.order_by('creation_time')[self.num_participants - 1].creation_time
            end_waiting_room = last_participant_creation_time
        t = 0
        performance_bonus = 0
        if end_waiting_room >= participant.creation_time:
            t = (end_waiting_room - participant.creation_time).total_seconds()
            performance_bonus = 1.75

        # keep to two decimal points otherwise doesn't work
        return round((t / 3600) * DOLLARS_PER_HOUR, 2) + performance_bonus

    def add_node_to_network(self, node, network):
        """Add node to the chain and receive transmissions."""
        network.add_node(node)
        source = network.nodes(type=Source)[0]  # find the source in the network
        source.connect(direction="to", whom=node)  # link up the source to the new node
        last_source_infos = source.infos()
        if not last_source_infos:
            source.transmit(to_whom=node)  # in networks.py code, transmit info to the new node
        node.receive()  # new node receives everything

    def info_post_request(self, node, info):
        """Run when a request to create an info is complete."""

        # Proceed with normal info post request
        for agent in node.neighbors():
            node.transmit(what=info, to_whom=agent)

    def create_node(self, participant, network):
        """Create a node for a participant."""
        # Check how many mafia members there are.
        # If there aren't enough, create another:
        num_mafioso = Node.query.filter_by(type="mafioso").count()
        if num_mafioso < self.num_mafia:
            mafioso = self.models.Mafioso(network=network,
                                          participant=participant)
            mafioso.fake_name = str(fake.name())
            mafioso.alive = 'True'
            return mafioso
        else:
            bystander = self.models.Bystander(network=network,
                                              participant=participant)
            bystander.fake_name = str(fake.name())
            bystander.alive = 'True'
            return bystander


extra_routes = Blueprint(
    'extra_routes',
    __name__,
    template_folder='templates',
    static_folder='static')


@extra_routes.route("/phase/<int:node_id>/<int:switches>/<string:was_daytime>",
                    methods=["GET"])
def phase(node_id, switches, was_daytime):
    try:
        exp = MafiaExperiment(db.session)
        this_node = Node.query.filter_by(id=node_id).one()
        net = Network.query.filter_by(id=this_node.network_id).one()
        nodes = Node.query.filter_by(network_id=net.id).order_by(
            'creation_time').all()
        node = nodes[-1]
        elapsed_time = timenow() - node.creation_time
        start_duration = 2 # this line ALSO gets set in experiment.js (hardcoded),
        # this is how long the "this person has been eliminatedTEMPORARY SWITCH BACK!" message gets displayed
        # setTimeout(function () { $("#stimulus").hide(); showExperiment(); }, 2000);
        day_round_duration = 150
        night_round_duration = 60
        break_duration = 10 # this line ALSO gets set in experiment.js (hardcoded),
        # this is how long the "The game will begin shortly..." message gets displayed
        # setTimeout(function () { $("#stimulus").hide(); get_transmissions(currentNodeId); }, 10000);
        daybreak_duration = day_round_duration + break_duration
        nightbreak_duration = night_round_duration + break_duration
        total_time = max(0, elapsed_time.total_seconds() - start_duration)
        if switches % 2 == 0:
            time = night_round_duration - (
                total_time -
                switches / 2 * daybreak_duration -
                (switches / 2) * nightbreak_duration
            ) % night_round_duration
        else:
            time = day_round_duration - (
                total_time -
                (switches + 1) / 2 * nightbreak_duration -
                (((switches+1) / 2) -1) * daybreak_duration
            ) % day_round_duration
        time = int(time)
        # victim_name = net.last_victim_name
        victim_name = None
        victim_type = None
        winner = None
        # winner = net.winner

        daytime = (net.daytime == 'True')
        phase_map = {'True': 'Phase Change to Daytime', 'False': 'Phase Change to Nighttime'}

        if was_daytime != net.daytime:
            victim_name = net.last_victim_name
            winner = net.winner
            source = net.nodes(type=Source)[0]
            last_source_info = Info.query.filter_by(
                origin_id=source.id,
                type='info'
            ).order_by('creation_time')[-1]
            if last_source_info.contents.split(':')[0] != phase_map[net.daytime]:
                if this_node.property2 == 'True':
                    source.transmit(to_whom=this_node)
        # If it's night but should be day, then call setup_daytime()
        elif not daytime and (
            int(total_time -
                switches / 2 * daybreak_duration
                - (switches / 2) * nightbreak_duration
                ) >= night_round_duration):
            victim_name, winner = net.setup_daytime()
            source = net.nodes(type=Source)[0]
            last_source_info = Info.query.filter_by(
                origin_id=source.id,
                type='info'
            ).order_by('creation_time')[-1]
            if last_source_info.contents.split(':')[0] != phase_map[net.daytime]:
                if this_node.property2 == 'True':
                    source.transmit(to_whom=this_node)
        # If it's day but should be night, then call setup_nighttime()
        elif daytime and (
            int(total_time -
                (switches + 1) / 2 * nightbreak_duration
                - (((switches + 1) / 2) - 1) * daybreak_duration
                ) >= day_round_duration):
            victim_name, winner = net.setup_nighttime()
            source = net.nodes(type=Source)[0]
            last_source_info = Info.query.filter_by(
                origin_id=source.id,
                type='info'
            ).order_by('creation_time')[-1]
            if last_source_info.contents.split(':')[0] != phase_map[net.daytime]:
                if this_node.property2 == 'True':
                    source.transmit(to_whom=this_node)


        exp.save()

        if victim_name:
            victim_type = Node.query.filter_by(property1=victim_name).one().type
        else:
            victim_type = None
            net.last_victim_name = None

        return Response(
            response=json.dumps({
                'time': time, 'daytime': net.daytime,
                'victim_name': victim_name, 'victim_type': victim_type, 'winner': winner
            }),
            status=200,
            mimetype='application/json')
    except Exception:
        db.logger.exception('Error fetching phase')
        return Response(
            status=403,
            mimetype='application/json')


@extra_routes.route("/live_participants/<int:node_id>/<int:get_all>",
                    methods=["GET"])
def live_participants(node_id, get_all):
    try:
        exp = MafiaExperiment(db.session)
        this_node = Node.query.filter_by(id=node_id).one()
        if get_all == 1:
            nodes = Node.query.filter_by(network_id=this_node.network_id,
                                         property2='True').all()
        else:
            nodes = Node.query.filter_by(network_id=this_node.network_id,
                                         property2='True',
                                         type='mafioso').all()
        participants = []
        for node in nodes:
            if node.property1 == this_node.property1:
                participants.append(node.property1 + ' (you!)')
            else:
                participants.append(node.property1)
        random.shuffle(participants)

        exp.save()

        return Response(
            response=json.dumps({'participants': participants}),
            status=200,
            mimetype='application/json')
    except Exception:
        db.logger.exception('Error fetching live participants')
        return Response(
            status=403,
            mimetype='application/json')


class Source(Source):

    __mapper_args__ = {
        "polymorphic_identity": "source"
    }

    def _contents(self):
        """Define the contents of new Infos.
        transmit() -> _what() -> create_information() -> _contents().
        """

        net = Network.query.filter_by(id=self.network_id).one()
        if net.property1 == 'True':
            if net.last_victim_name:
                return "Phase Change to Daytime: Victim - " + net.last_victim_name
            else:
                return "Phase Change to Daytime"
        else:
            if net.last_victim_name:
                return "Phase Change to Nighttime: Victim - " + net.last_victim_name
            else:
                return "Phase Change to Nighttime"
