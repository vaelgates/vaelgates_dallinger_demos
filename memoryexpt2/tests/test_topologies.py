import mock
import pytest
from dallinger.models import Participant
from dallinger.nodes import Agent


def assertItemsEqual(a, b):
    temp = b[:]
    for item in a:
        assert item in temp
        temp.remove(item)
    assert not temp


class TestBaseTopology(object):

    @pytest.fixture
    def topology(self, exp_module):

        class TestTopology(exp_module.topologies.BaseTopology):
            nickname = u'test'
            all_edges = [(0, 1), (0, 2), (0, 3), (2, 3)]

        return TestTopology()

    def test_potential_partners_returns_predefined_node_indexes(self, topology):
        assert topology.potential_partners(0) == [1, 2, 3]
        assert topology.potential_partners(1) == [0]
        assert topology.potential_partners(2) == [0, 3]
        assert topology.potential_partners(3) == [0, 2]


@pytest.mark.usefixtures('exp_module')
class TestTopology(object):

    @pytest.fixture
    def topology(self, exp_module):
        return exp_module.topologies.Baby2(max_size=3)

    @pytest.fixture
    def second_topology(self, exp_module):
        return exp_module.topologies.Baby2(max_size=3)

    @pytest.fixture
    def nodes(self, topology, db_session, n=3):
        nodes = []
        for i in range(n):
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

    def test_topology_handles_out_of_order_nodes(self, db_session, topology, second_topology, dbview):
        """This tests that the topology based networks do not directly use participant or node
        primary keys in determining where in the preset edge graph a given node is"""
        # Fill two networks simultaneously with newly created nodes
        self.nodes(topology, db_session, n=2)
        self.nodes(second_topology, db_session, n=2)
        self.nodes(topology, db_session, n=1)
        self.nodes(second_topology, db_session, n=1)

        # These topologies have non-contiguous node ids
        assert {node.id for node in topology.nodes()} == {1, 2, 5}
        assert {node.id for node in second_topology.nodes()} == {3, 4, 6}

        # Their edge graph is still internally consistent
        assertItemsEqual([
                set(neighbor.id for neighbor in node.neighbors())
                for node in topology.nodes()
            ],
            [{2, 5}, {1}, {1}]
        )

        assertItemsEqual([
                set(neighbor.id for neighbor in node.neighbors())
                for node in second_topology.nodes()
            ],
            [{4, 6}, {3}, {3}]
        )


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

    def test_single_pair_is_mutually_connected(self, a, experiment):
        net = experiment.networks()[0]
        p1 = a.participant(worker_id='1')
        p2 = a.participant(worker_id='2')
        node1 = a.node(network=net, participant=p1)
        node2 = a.node(network=net, participant=p2)

        experiment.add_node_to_network(node1, net)
        experiment.add_node_to_network(node2, net)

        node1.is_connected(node2)
        node2.is_connected(node1)

    def test_ten_pairs(self, a, experiment, dbview):
        net = experiment.networks()[0]
        nodes = []
        participants = [a.participant(worker_id=str(i)) for i in range(20)]
        for p in participants:
            node = experiment.create_node(network=net, participant=p)
            experiment.add_node_to_network(node, net)
            nodes.append(node)

        assert dbview.partner_indexes(nodes[0]) == [
            1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 17, 19
        ]

    def test_perfect_full_network(self, a, experiment, dbview):
        net = experiment.networks()[0]
        nodes = []
        participants = [a.participant(worker_id=str(i)) for i in range(34)]
        for p in participants:
            node = experiment.create_node(network=net, participant=p)
            experiment.add_node_to_network(node, net)
            nodes.append(node)

        for idx, node in enumerate(nodes):
            assert dbview.partner_indexes(node) == net.potential_partners(idx)
