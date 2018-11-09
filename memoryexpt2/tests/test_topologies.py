import mock
import pytest
from dallinger.models import Node
from dallinger.models import Vector


@pytest.mark.usefixtures('exp_module')
class TestKarateClub(object):

    @pytest.fixture
    def source(self, exp_module):
        exp_module.FreeRecallListSource._contents = mock.Mock(return_value='')

    @pytest.fixture
    def kclub(self, db_session, active_config, exp_klass, source):
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

    def test_single_pair_is_mutually_connected(self, a, kclub):
        net = kclub.networks()[0]
        p1 = a.participant(worker_id='1')
        p2 = a.participant(worker_id='2')
        node1 = a.node(network=net, participant=p1)
        node2 = a.node(network=net, participant=p2)

        kclub.add_node_to_network(node1, net)

        node1.is_connected(node2)
        node2.is_connected(node1)

    def test_ten_pairs(self, a, kclub):
        net = kclub.networks()[0]
        # participants have IDs '1 through '20':
        participants = [a.participant(worker_id=str(i)) for i in range(1, 21)]
        for p in participants:
            node = kclub.create_node(network=net, participant=p)
            kclub.add_node_to_network(node, net)

        assert self.partners_of('1') == [
            2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 18, 20
        ]

    def test_perfect_full_network(self, a, kclub):
        net = kclub.networks()[0]
        # participants have IDs '1 through '34':
        participants = [a.participant(worker_id=str(i)) for i in range(1, 35)]
        for p in participants:
            node = kclub.create_node(network=net, participant=p)
            kclub.add_node_to_network(node, net)

        assert self.partners_of('1') == [
            2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 18, 20, 22, 32
        ]

        assert self.partners_of('1') == kclub.topology.potential_partners(1)
        assert self.partners_of('5') == kclub.topology.potential_partners(5)
        assert self.partners_of('13') == kclub.topology.potential_partners(13)
        assert self.partners_of('34') == kclub.topology.potential_partners(34)

    def test_with_waiting_room_dropouts(self, a, kclub):
        net = kclub.networks()[0]
        # participants have IDs '1 through '34':
        participants = [a.participant(worker_id=str(i)) for i in range(1, 35)]
        for p in participants:
            if p.id in (2, 3):
                continue
            node = kclub.create_node(network=net, participant=p)
            kclub.add_node_to_network(node, net)

        assert self.partners_of('1') == [
            4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 18, 20, 22, 32
        ]

    def test_real_participant_list(self, a, kclub):
        net = kclub.networks()[0]
        actually_participate = [
            1, 4, 7, 11, 13, 16, 21, 22, 24, 28, 29, 30, 33, 36, 37, 38, 39, 42,
            43, 44, 45, 46, 47, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60,
            61, 62, 63, 64, 65, 67, 69
        ]
        participants = [a.participant(worker_id=str(i)) for i in range(1, 70)]

        for p in participants:
            if p.id not in actually_participate:
                continue
            node = kclub.create_node(network=net, participant=p)
            kclub.add_node_to_network(node, net)

        vectors = self.participant_vectors()
        ordered = [tuple(sorted(pair)) for pair in vectors]
        deduped = sorted(list(set(sorted(ordered))))

        assert deduped == [
            (1, 4), (1, 7), (1, 11), (1, 13), (1, 22), (4, 13), (16, 33),
            (21, 33), (24, 28), (24, 30), (24, 33), (30, 33)
        ]
