import mock
import pytest
from dallinger.models import Node
from dallinger.models import Participant
from dallinger.models import Vector
from dallinger.nodes import Agent


@pytest.mark.usefixtures('exp_module')
class TestTopology(object):

    @pytest.fixture
    def topology(self, exp_module):
        return exp_module.topologies.Baby2(max_size=3)

    @pytest.fixture
    def nodes(self, topology, db_session):
        nodes = []
        for i in range(3):
            participant = Participant(
                recruiter_id='testing',
                worker_id='worker_%d' % i,
                assignment_id='assignment_%d' % i,
                hit_id='hit_%d' % i,
                mode='testing',
                fingerprint_hash='fingerprint_%d' % i,
            )
            db_session.add(participant)
            participant.status = 'working'
            node = Agent(network=topology, participant=participant)
            db_session.add(node)
            topology.add_node(node)
            nodes.append(node)
        return nodes

    def test_topology_links_based_on_edges(self, topology, nodes):
        assert len(nodes) == 3
        assert len(topology.nodes()) == 3
        assert nodes[0].neighbors() == [nodes[1], nodes[2]]
        assert nodes[1].neighbors() == [nodes[0]]
        assert nodes[2].neighbors() == [nodes[0]]


@pytest.mark.usefixtures('exp_module')
class TestKarateClub(object):

    @pytest.fixture
    def source(self, exp_module):
        exp_module.FreeRecallListSource._contents = mock.Mock(return_value='')

    @pytest.fixture
    def experiment(self, db_session, active_config, exp_klass, source):
        active_config.extend({'mexp_topology': u'karateclub'}, strict=True)
        chatroom = exp_klass(db_session)
        chatroom.app_id = 'test app'
        chatroom.exp_config = active_config

        yield chatroom
        chatroom.session.rollback()
        chatroom.session.close()

    def partners_of(self, participant_id):
        node = Node.query.filter_by(participant_id=participant_id).one()
        return [n.participant_id for n in node.neighbors()]

    def participant_vectors(self):
        vectors = [
            (v.origin.participant_id, v.destination.participant_id)
            for v in Vector.query.all()
            if v.origin.participant_id is not None
        ]

        return sorted(vectors)

    def unique_participant_vectors(self):
        vectors = self.participant_vectors()
        ordered = [tuple(sorted(pair)) for pair in vectors]
        deduped = sorted(list(set(sorted(ordered))))

        return deduped

    def test_single_pair_is_mutually_connected(self, a, experiment, db_session):
        net = experiment.networks()[0]
        p1 = a.participant(worker_id='1')
        p2 = a.participant(worker_id='2')
        node1 = a.node(network=net, participant=p1)
        node2 = a.node(network=net, participant=p2)
        db_session.add(node1)
        db_session.add(node2)

        experiment.add_node_to_network(node1, net)
        experiment.add_node_to_network(node2, net)

        node1.is_connected(node2)
        node2.is_connected(node1)

    def test_ten_pairs(self, a, experiment):
        net = experiment.networks()[0]
        # participants have IDs '1 through '20':
        participants = [a.participant(worker_id=str(i)) for i in range(1, 21)]
        for p in participants:
            node = experiment.create_node(network=net, participant=p)
            experiment.add_node_to_network(node, net)

        assert self.partners_of('1') == [
            2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 18, 20
        ]

    def test_perfect_full_network(self, a, experiment):
        net = experiment.networks()[0]
        # participants have IDs '1 through '34':
        participants = [a.participant(worker_id=str(i)) for i in range(1, 35)]
        for p in participants:
            node = experiment.create_node(network=net, participant=p)
            experiment.add_node_to_network(node, net)

        assert self.partners_of('1') == [
            2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 18, 20, 22, 32
        ]

        assert self.partners_of('1') == net.potential_partners(1)
        assert self.partners_of('5') == net.potential_partners(5)
        assert self.partners_of('13') == net.potential_partners(13)
        assert self.partners_of('34') == net.potential_partners(34)
        assert self.unique_participant_vectors() == net.participant_edges()
