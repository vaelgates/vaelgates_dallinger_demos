"""Define kinds of nodes: agents, sources, and environments."""
import logging
from sqlalchemy.ext.hybrid import hybrid_property
from dallinger.models import Node, Network, Info, timenow
from dallinger.nodes import Source
from random import choice, seed, random
from dallinger import db
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

    def fail_bystander_vectors(self):
        """Fails Vectors connecting Bystanders (non-Mafia).
        """
        mafiosi = self.live_mafiosi()
        for v in self.vectors():  # returns non-failed Vectors only
            if not isinstance(v.origin, Source) and not (
                    v.origin in mafiosi and v.destination in mafiosi):
                v.fail()

    def vote(self, nodes):
        phase_map = {'True': 'Phase Change to Daytime', 'False': 'Phase Change to Nighttime'}
        votes = {}
        for node in nodes:
            vote = None
            node_votes = Info.query.filter_by(
                origin_id=node.id,
                type='vote'
            ).order_by('creation_time')
            if node_votes.first() is not None:
                infos = Info.query.filter_by(
                                    origin_id=self.nodes(type=Source)[0].id,
                                    type='info'
                                    ).order_by('creation_time')
                phase_start_time = infos[-1].creation_time
                if infos[-1].contents.split(': ')[0] == phase_map[self.daytime]:
                    phase_start_time = infos[-2].creation_time
                if (node_votes[-1].creation_time - phase_start_time).total_seconds() > 0:
                    node_vote = node_votes[-1].contents.split(': ')[1]
                    if Node.query.filter_by(
                            property1=node_vote).one().property2 == 'True':
                        vote = node_vote
            if vote:
                if vote in votes:
                    votes[vote] += 1
                else:
                    votes[vote] = 1
        # sorted_kv = sorted(votes.items(), key=lambda kv: kv[0])
        if votes:
            victim_name, _ = max(votes.items(), key=lambda kv: kv[1] + random())
            self.last_victim_name = victim_name
            victim_node = Node.query.filter_by(property1=victim_name).one()
            self.kill_victim(victim_node)
        else:
            victim_name = None
            self.last_victim_name = None
        return victim_name

    def kill_victim(self, victim_node):
        """Don't fail the Node itself, but fail all it's related objects.
        TODO: explain why not just victim_node.fail()
        """
        victim_node.alive = 'False'
        for v in victim_node.vectors():
            v.fail()
        for i in victim_node.infos():
            i.fail()
        for t in victim_node.transmissions(direction="all"):
            t.fail()
        for t in victim_node.transformations():
            t.fail()
        victim_node.deathtime = timenow()

    def setup_daytime(self):
        self.daytime = 'True'
        mafiosi = self.live_mafiosi()
        victim_name = self.vote(mafiosi)
        mafiosi = self.live_mafiosi()
        nodes = self.live_nodes()
        winner = None
        if len(mafiosi) >= len(nodes) - len(mafiosi):
            winner = 'mafia'
            self.winner = winner
            return victim_name, winner
        elif len(mafiosi) == 0:
            winner = 'bystanders'
            self.winner = winner
            return victim_name, winner
        for n in nodes:
            for m in nodes:
                if n != m:
                    n.connect(whom=m, direction="to")
        return victim_name, winner

    def setup_nighttime(self):
        self.daytime = 'False'
        nodes = self.live_nodes()
        victim_name = self.vote(nodes)
        mafiosi = self.live_mafiosi()
        nodes = self.live_nodes()
        winner = None
        if len(mafiosi) >= len(nodes) - len(mafiosi):
            winner = 'mafia'
            self.winner = winner
            return victim_name, winner
        elif len(mafiosi) == 0:
            winner = 'bystanders'
            self.winner = winner
            return victim_name, winner
        self.fail_bystander_vectors()
        return victim_name, winner

    def live_nodes(self):
        """Living bystanders and mafios"""
        nodes = Node.query.filter_by(
            network_id=self.id, property2='True'
        ).all()
        return nodes

    def live_mafiosi(self):
        mafiosi = Node.query.filter_by(
            network_id=self.id, property2='True', type='mafioso'
        ).all()
        return mafiosi
