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
from collections import defaultdict
from joblib import load
import json
import os
import csv


# DOLLARS_PER_HOUR = 5.0
DOLLARS_PER_HOUR = 7.0
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


class MafiaExperiment(dlgr.experiments.Experiment):
    """Define the structure of the experiment."""

    def __init__(self, session):
        """Initialize the experiment."""
        super(MafiaExperiment, self).__init__(session)
        import models
        self.models = models
        # self.skip_instructions = False  # If True, you'll go directly to /waiting
        self.skip_instructions = True  # If True, you'll go directly to /waiting
        self.experiment_repeats = 1
        # self.num_participants = 10
        self.num_participants = 3
        # self.num_mafia = 2
        self.num_mafia = 1
        # Note: can't do * 2.5 here, won't run even if the end result isn't an integer
        # self.initial_recruitment_size = self.num_participants * 3
        # self.initial_recruitment_size = self.num_participants * 2
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
        mafia_network.num_victims = 0
        mafia_network.num_rand = 0
        return mafia_network

    def is_overrecruited(self, waiting_count):
        """Returns True if the number of people waiting is in excess of the
        total number expected, indicating that this and subsequent users should
        skip the experiment. A quorum value of 0 means we don't limit
        recruitment, and always return False.

        Additionally, we check if there are any Participant Nodes already
        present. If there are, this means the experiment has already started, a
        and we're "overrecruited" by definition. We do this to prevent anyone
        from joining the experiment late.
        """
        if not self.quorum:
            return False
        if waiting_count > self.quorum:
            return True
        # Check for existing Participant Nodes, which indicates experiment
        # has started:
        for network in self.networks():
            if len(network.nodes(type=Node)) > 1:
                return True
        # for network in self.networks():
        #     if network.nodes(type=Participant):
        #         return True
        return False

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
        # day_round_duration = 150
        day_round_duration = 60
        # night_round_duration = 60
        night_round_duration = 10
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
        victim_name = None
        victim_type = None
        winner = None

        daytime = (net.daytime == 'True')
        phase_map = {'True': 'Phase Change to Daytime', 'False': 'Phase Change to Nighttime'}

        if was_daytime != net.daytime:
            victim_name = net.last_victim_name
            db.logger.exception('Victim Name (as copied from network)')
            db.logger.exception(victim_name)
            winner = net.winner
            db.logger.exception('Winner')
            db.logger.exception(winner)
            net.node_random()
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
            db.logger.exception('Winner')
            db.logger.exception(winner)
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
            db.logger.exception('Winner')
            db.logger.exception(winner)
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
            db.logger.exception('Victim Type')
            db.logger.exception(victim_type)
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


@extra_routes.route("/suspected_mafia/<int:node_id>/<int:get_all>",
                    methods=["GET"])
def suspected_mafia(node_id, get_all):
    try:
        exp = MafiaExperiment(db.session)
        this_node = Node.query.filter_by(id=node_id).one()
        infos = Info.query.filter_by().order_by('creation_time')
        daytime_infos = defaultdict(lambda: defaultdict(list))
        night = False
        victims = []
        num_rounds = 0
        round_start_time = 0
        nodes = Node.query.filter_by(network_id=this_node.network_id,
                                     property2='True').all()
        participants = [node.property1 for node in nodes]
        type_map = {'bystander': 'bystanders', 'mafioso': 'mafia'}
        factions = {node.property1: type_map[node.type] for node in nodes}
        daytime_infos = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for info in infos:
            if 'Phase Change to Nighttime' in info.contents:
                night = True
                if 'Victim' in info.contents:
                    victims.append(info.contents.split('- ')[1])
                else:
                    victims.append(None)
                continue
            elif 'Phase Change to Daytime' in info.contents:
                if night:
                    night = False
                    num_rounds += 1
                    round_start_time = info.creation_time
                continue
            if not night:
                if info.type == 'vote':
                    # voter, votee = info.contents.split(': ')
                    # daytime_infos[0][factions[voter]][voter].append((num_rounds, votee, (info.creation_time - round_start_time).total_seconds()))
                    continue
                else:
                    texter, text = info.contents.split(': ')
                    daytime_infos[0][factions[texter]][texter].append((num_rounds, text, (info.creation_time - round_start_time).total_seconds()))
        # cwd = os.getcwd()
        # print(cwd)
        # db.logger.exception('cwd')
        # db.logger.exception(cwd)
        with open('mafia/daytime_infos.json', 'w') as daytime_infos_file:
            json.dump(daytime_infos, daytime_infos_file)
        # model = 'mafia_other_time_2_mes_tiny_uncased_1000/'
        os.system("export BERT_BASE_DIR=uncased_L-2_H-128_A-2")
        os.system("export DATA_DIR=mafia")
        os.system("python3 run_classifier.py \
  --task_name=PredictMafia \
  --do_train=false \
  --do_eval=false \
  --do_predict=true \
  --do_lower_case=true \
  --data_dir=$DATA_DIR \
  --vocab_file=$BERT_BASE_DIR/vocab.txt \
  --bert_config_file=$BERT_BASE_DIR/bert_config.json \
  --max_seq_length=128 \
  --train_batch_size=32 \
  --learning_rate=2e-5 \
  --num_train_epochs=1000.0 \
  --output_dir=mafia_other_time_2_mes_tiny_uncased_1000/")
  #       os.system("python3 run_classifier.py \
  # --task_name=PredictMafia \
  # --do_train=false \
  # --do_eval=false \
  # --do_predict=true \
  # --do_lower_case=true \
  # --data_dir=$DATA_DIR \
  # --vocab_file=$BERT_BASE_DIR/vocab.txt \
  # --bert_config_file=$BERT_BASE_DIR/bert_config.json \
  # --max_seq_length=128 \
  # --train_batch_size=32 \
  # --learning_rate=2e-5 \
  # --num_train_epochs=1000.0 \
  # --output_dir=mafia_other_time_2_mes_tiny_uncased_1000/ 2>&1 | tee $DATA_DIR/predict_mafia")
        players = [player for group in daytime_infos[game] for player in daytime_infos[game][group]]
        with open('mafia_other_time_2_mes_tiny_uncased_1000/test_results.tsv') as test_results_file:
            probs = csv.reader(test_results_file, delimiter='\t')
            participants = [[players[i], mafia_prob] for i, (mafia_prob, _) in enumerate(probs)]
        # for info in infos:
        #     if 'Phase Change to Nighttime' in info.contents:
        #         night = True
        #         if 'Victim' in info.contents:
        #             victims.append(info.contents.split('- ')[1])
        #         else:
        #             victims.append(None)
        #         continue
        #     elif 'Phase Change to Daytime' in info.contents:
        #         if night:
        #             night = False
        #             num_rounds += 1
        #             round_start_time = info.creation_time
        #         continue
        #     if not night:
        #         if info.type == 'vote':
        #             voter, votee = info.contents.split(': ')
        #             daytime_infos[voter][num_rounds].append((votee, (info.creation_time - round_start_time).total_seconds()))
        #         else:
        #             texter, text = info.contents.split(': ')
        #             daytime_infos[texter][num_rounds].append((len(text), (info.creation_time - round_start_time).total_seconds()))
        # # nodes = Node.query.filter_by(network_id=this_node.network_id,
        # #                              property2='True').all()
        # # participants = [node.property1 for node in nodes]
        # [daytime_infos[participant][round] for participant in participants for round in range(1, num_rounds)]
        # features = defaultdict(list)
        # for participant in daytime_infos:
        #     prop_round_votes = 0.
        #     prop_round_majority_votes = 0.
        #     prop_round_texts_before_votes = 0.
        #     prop_round_texts = 0.
        #     mean_time_votes = 0.
        #     mean_time_texts = 0.
        #     mean_num_texts = 0.
        #     mean_len_texts = 0.
        #     for round in daytime_infos[participant]:
        #         found_text = False
        #         for i, act in enumerate(daytime_infos[participant][round]):
        #             if type(act[0]) == int:
        #                 if i == 0:
        #                     prop_round_texts_before_votes += 1
        #                 if not found_text:
        #                     prop_round_texts += 1
        #                     found_text = True
        #                 mean_num_texts += 1
        #                 mean_len_texts += act[0]
        #                 mean_time_texts += act[1]
        #             elif type(act[0]) == str:
        #                 prop_round_votes += 1
        #                 if act[0] == victims[round]:
        #                     prop_round_majority_votes += 1
        #                 mean_time_votes += act[1]
        #     features[participant].append(prop_round_votes / (num_rounds - 1))
        #     # if prop_round_votes:
        #     #     features[participant].append(prop_round_majority_votes / prop_round_votes)
        #     # else:
        #     #     features[participant].append(None)
        #     features[participant].append(prop_round_majority_votes / (num_rounds - 1))
        #     # if prop_round_votes:
        #     #     features[participant].append(prop_round_texts_before_votes / prop_round_votes)
        #     # else:
        #     #     features[participant].append(None)
        #     features[participant].append(prop_round_texts_before_votes / (num_rounds - 1))
        #     features[participant].append(prop_round_texts / (num_rounds - 1))
        #     # if prop_round_votes:
        #     #     features[participant].append(mean_time_votes / prop_round_votes)
        #     # else:
        #     #     features[participant].append(None)
        #     features[participant].append(mean_time_votes / (num_rounds - 1))
        #     # if prop_round_texts:
        #     #     features[participant].append(mean_time_texts / prop_round_texts)
        #     # else:
        #     #     features[participant].append(None)
        #     features[participant].append(mean_time_texts / (num_rounds - 1))
        #     features[participant].append(mean_num_texts / (num_rounds - 1))
        #     if mean_num_texts:
        #         features[participant].append(mean_len_texts / mean_num_texts)
        #     else:
        #         features[participant].append(0.)
        # participants = list(features.values())
        #
        # model = load('mafia_model.joblib')
        # probs = model.predict_proba(list(features.values()))
        # participants = [[list(features.keys())[i], mafia_prob] for i, (mafia_prob, _) in enumerate(probs)]
        exp.save()

        return Response(
            response=json.dumps({'participants': participants}),
            status=200,
            mimetype='application/json')
    except Exception:
        db.logger.exception('Error fetching suspected mafia')
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
