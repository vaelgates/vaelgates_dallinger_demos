"""Define kinds of nodes: agents, sources, and environments."""
import logging
from sqlalchemy.ext.hybrid import hybrid_property
from dallinger.models import Node, Network, Info, timenow
from dallinger.nodes import Source
from random import seed, random
from dallinger import db
from datetime import datetime

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
seed(42)

logger = logging.getLogger(__name__)


class Text(Info):
    """A text"""

    __mapper_args__ = {"polymorphic_identity": "text"}


class Vote(Info):
    """A vote"""

    __mapper_args__ = {"polymorphic_identity": "vote"}


class Bystander(Node):
    """Bystander"""

    __mapper_args__ = {"polymorphic_identity": "bystander"}

    @hybrid_property
    def fake_name(self):
        """Convert property1 to fake name."""
        try:
            return self.property1
        except TypeError:
            return None

    @fake_name.setter
    def fake_name(self, name):
        """Make name settable."""
        self.property1 = name

    @fake_name.expression
    def fake_name(self):
        """Make name queryable."""
        return self.property1

    @hybrid_property
    def alive(self):
        """Convert property2 to alive."""
        try:
            return self.property2
        except TypeError:
            return None

    @alive.setter
    def alive(self, is_alive):
        """Make alive settable."""
        self.property2 = is_alive

    @alive.expression
    def alive(self):
        """Make alive queryable."""
        return self.property2

    @hybrid_property
    def deathtime(self):
        """Convert property3 to death time."""
        try:
            return self.property3
        except TypeError:
            return None

    @deathtime.setter
    def deathtime(self, death_time):
        """Make death time settable."""
        self.property3 = death_time

    @deathtime.expression
    def deathtime(self):
        """Make death time queryable."""
        return self.property3


class Mafioso(Bystander):
    """Member of the mafia."""

    __mapper_args__ = {"polymorphic_identity": "mafioso"}


class MafiaNetwork(Network):
    """A mafia network that switches between FullyConnected
    for all and only mafia nodes."""

    __mapper_args__ = {"polymorphic_identity": "mafia-network"}

    def add_node(self, node):
        """Add a node, connecting it to other mafia if mafioso."""
        if node.type == "mafioso":
            other_mafiosi = [n for n in self.live_mafiosi() if n.id != node.id]
            for n in other_mafiosi:
                try:
                    node.connect(direction="both", whom=n)
                except ValueError:
                    logger.error("Error connecting Mafioso!", exc_info=1)

    def add_source(self, source):
        """Connect the source to all existing other nodes."""
        nodes = [n for n in self.nodes() if not isinstance(n, Source)]
        source.connect(whom=nodes)

    @hybrid_property
    def daytime(self):
        """Convert property1 to daytime."""
        try:
            return self.property1
        except TypeError:
            return None

    @daytime.setter
    def daytime(self, is_daytime):
        """Make time settable."""
        self.property1 = is_daytime

    @daytime.expression
    def daytime(self):
        """Make time queryable."""
        return self.property1

    @hybrid_property
    def winner(self):
        """Convert property2 to winner."""
        try:
            return self.property2
        except TypeError:
            return None

    @winner.setter
    def winner(self, is_winner):
        """Make time settable."""
        self.property2 = is_winner

    @winner.expression
    def winner(self):
        """Make winner queryable."""
        return self.property2

    @hybrid_property
    def last_victim_name(self):
        """Convert property3 to last_victim_name."""
        try:
            return self.property3
        except TypeError:
            return None

    @last_victim_name.setter
    def last_victim_name(self, is_last_victim_name):
        """Make last_victim_name settable."""
        self.property3 = is_last_victim_name

    @last_victim_name.expression
    def last_victim_name(self):
        """Make last_victim_name queryable."""
        return self.property3

    @hybrid_property
    def num_victims(self):
        """Convert property4 to num_victims."""
        try:
            return int(self.property4)
        except TypeError:
            return None

    @num_victims.setter
    def num_victims(self, is_num_victims):
        """Make num_victims settable."""
        self.property4 = is_num_victims

    @num_victims.expression
    def num_victims(self):
        """Make num_victims queryable."""
        return self.property4

    @hybrid_property
    def num_rand(self):
        """Convert property5 to num_rand."""
        try:
            return int(self.property5)
        except TypeError:
            return None

    @num_rand.setter
    def num_rand(self, num_random):
        """Make num_rand settable."""
        self.property5 = num_random

    @num_rand.expression
    def num_rand(self):
        """Make num_rand queryable."""
        return self.property5

    def fail_bystander_vectors(self):
        """Fails Vectors connecting Bystanders (non-Mafia).
        """
        mafiosi = self.live_mafiosi()
        for v in self.vectors():  # returns non-failed Vectors only
            if not isinstance(v.origin, Source) and not (
                    v.origin in mafiosi and v.destination in mafiosi):
                v.fail()

    def node_random(self):
        for _ in range(self.num_rand):
            random()

    def vote(self, nodes):
        phase_map = {'True': 'Phase Change to Daytime', 'False': 'Phase Change to Nighttime'}
        votes = {}
        infos = Info.query.filter_by(
                            origin_id=self.nodes(type=Source)[0].id,
                            type='info'
                            ).order_by('creation_time')
        phase_start_time = infos[-1].creation_time
        i = 0
        while infos[-1 - i].contents.split(': ')[0] == phase_map[self.daytime]:
            i += 1
            phase_start_time = infos[-1 - i].creation_time
        db.logger.exception('Phase Start Time')
        db.logger.exception(phase_start_time)
        for node in nodes:
            vote = None
            node_votes = Info.query.filter_by(
                origin_id=node.id,
                type='vote'
            ).order_by('creation_time')
            if node_votes.first() and (node_votes[-1].creation_time - phase_start_time).total_seconds() > 0:
                node_vote = node_votes[-1].contents.split(': ')[1]
                vote = node_vote
            db.logger.exception('Node')
            db.logger.exception(node)
            db.logger.exception('Node Vote')
            db.logger.exception(vote)
            if vote:
                if vote in votes:
                    votes[vote] += 1
                else:
                    votes[vote] = 1
        db.logger.exception('Votes')
        db.logger.exception(votes)
        sorted_kv = sorted(votes.items(), key=lambda kv: kv[0])
        if votes:
            victim_name, num_votes = max(sorted_kv, key=lambda kv: kv[1] + random())
            self.last_victim_name = victim_name
            num_random = len([v for _, v in votes.items() if v == num_votes])
            self.num_rand = num_random
            victim_node = Node.query.filter_by(property1=victim_name).one()
            db.logger.exception('Victim Node')
            db.logger.exception(victim_node)
            self.kill_victim(victim_node)
        else:
            self.num_rand = 0
            victim_name = None
            self.last_victim_name = None
            db.logger.exception('Victim Node')
            db.logger.exception(self.last_victim_name)
            db.logger.exception('Victim Death Time')
            db.logger.exception(None)
            db.logger.exception('Victim Count')
            db.logger.exception(self.num_victims)
        return victim_name

    def kill_victim(self, victim_node):
        """Don't fail the Node itself, but fail all it's related objects.
        TODO: explain why not just victim_node.fail()
        """
        victim_node.alive = 'False'
        victim_node.deathtime = timenow()
        db.logger.exception('Victim Death Time')
        db.logger.exception(victim_node.deathtime)
        self.num_victims += 1
        db.logger.exception('Victim Count')
        db.logger.exception(self.num_victims)
        for v in victim_node.vectors():
            v.fail()
        for i in victim_node.infos():
            i.fail()
        for t in victim_node.transmissions(direction="all"):
            t.fail()
        for t in victim_node.transformations():
            t.fail()

    def setup_daytime(self):
        self.daytime = 'True'
        victim_nodes = self.victim_nodes()
        db.logger.exception('Daytime - Past Victim Nodes')
        db.logger.exception(victim_nodes)
        db.logger.exception('Daytime - Victim Count')
        db.logger.exception(self.num_victims)
        if len(victim_nodes) > self.num_victims:
            self.node_random()
            self.last_victim_name = victim_nodes[-1].fake_name
            db.logger.exception('Daytime - Victim')
            db.logger.exception(self.last_victim_name)
            return self.last_victim_name, self.get_winner()
        mafiosi = self.live_mafiosi()
        victim_name = self.vote(mafiosi)
        db.logger.exception('Daytime Victim')
        db.logger.exception(victim_name)
        self.connect_all_nodes()
        return victim_name, self.get_winner()

    def setup_nighttime(self):
        self.daytime = 'False'
        victim_nodes = self.victim_nodes()
        db.logger.exception('Nighttime - Past Victim Nodes')
        db.logger.exception(victim_nodes)
        db.logger.exception('Nighttime - Victim Count')
        db.logger.exception(self.num_victims)
        if len(victim_nodes) > self.num_victims:
            self.node_random()
            self.last_victim_name = victim_nodes[-1].fake_name
            db.logger.exception('Nighttime - Victim')
            db.logger.exception(self.last_victim_name)
            return self.last_victim_name, self.get_winner()
        nodes = self.live_nodes()
        victim_name = self.vote(nodes)
        db.logger.exception('Nighttime Victim')
        db.logger.exception(victim_name)
        self.fail_bystander_vectors()
        return victim_name, self.get_winner()

    def connect_all_nodes(self):
        nodes = self.live_nodes()
        for n in nodes:
            for m in nodes:
                if n != m:
                    n.connect(whom=m, direction="to")

    def victim_nodes(self):
        """Victim bystanders and mafiosi"""
        nodes = Node.query.filter_by(
            network_id=self.id,
            property2='False'
        ).order_by('property3').all()
        return nodes

    def live_nodes(self):
        """Living bystanders and mafiosi"""
        nodes = Node.query.filter_by(
            network_id=self.id, property2='True', failed='False'
        ).all()
        return nodes

    def live_mafiosi(self):
        """Living mafiosi"""
        mafiosi = Node.query.filter_by(
            network_id=self.id, property2='True', failed='False', type='mafioso'
        ).all()
        return mafiosi

    def get_winner(self):
        nodes = self.live_nodes()
        db.logger.exception('Live Nodes')
        db.logger.exception(nodes)
        mafiosi = self.live_mafiosi()
        db.logger.exception('Live Mafiosi')
        db.logger.exception(mafiosi)
        if len(mafiosi) >= len(nodes) - len(mafiosi):
            winner = 'mafia'
            self.winner = winner
            return winner
        elif len(mafiosi) == 0:
            winner = 'bystanders'
            self.winner = winner
            return winner
        else:
            return self.winner
