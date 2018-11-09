import logging
from dallinger.networks import Empty
from dallinger.networks import FullyConnected

logger = logging.getLogger(__name__)


class Topology(object):
    """Abstract base class."""

    network = Empty
    nickname = None

    def participant_edges(self):
        return [(edge[0] + 1, edge[1] + 1) for edge in self. edges()]

    def edges(self):
        return list(self.all_edges)

    def potential_partners(self, participant_id):
        partners = []
        for pair in self.participant_edges():
            if participant_id in pair:
                partner_id = [pid for pid in pair if pid != participant_id][0]
                partners.append(partner_id)

        return sorted(partners)

    def __repr__(self):
        return "%s (%s)" % (self.__class__.__name__, self.network)


class Nominal(Topology):
    """Participants play in isolation, with no transmissions to or from
    others.
    """
    nickname = u'nominal'
    all_edges = []


class Collaborative(Topology):
    """All participants are connected to one another."""
    network = FullyConnected
    nickname = u'collaborative'
    all_edges = []


class Baby2(Topology):
    nickname = u'baby2'
    all_edges = [(0, 1), (0, 2)]


class Baby4(Topology):
    nickname = u'baby4'
    all_edges = [(0, 1), (0, 2), (0, 3), (2, 3)]


class KarateClub(Topology):
    """KarateClub network.

    Data originally from: http://vlado.fmf.uni-lj.si/pub/networks/data/Ucinet/UciData.htm#zachary

    Formatting as described in:
    https://networkx.github.io/documentation/networkx-1.9/examples/graph/karate_club.html

    An undirected, unweighted network showing connections between 34 members
    of Zachary's karate club.

    Reference:
    Zachary W. (1977).
    An information flow model for conflict and fission in small groups.
    Journal of Anthropological Research, 33, 452-473.
    """
    nickname = u'karateclub'
    all_edges = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8),
        (0, 10), (0, 11), (0, 12), (0, 13), (0, 17), (0, 19), (0, 21), (0, 31), (1, 17),
        (1, 2), (1, 3), (1, 21), (1, 19), (1, 7), (1, 13), (1, 30), (2, 3), (2, 32),
        (2, 7), (2, 8), (2, 9), (2, 27), (2, 28), (2, 13), (3, 7), (3, 12), (3, 13), (4, 10),
        (4, 6), (5, 16), (5, 10), (5, 6), (6, 16), (8, 32), (8, 30), (8, 33), (9, 33),
        (13, 33), (14, 32), (14, 33), (15, 32), (15, 33), (18, 32), (18, 33), (19, 33),
        (20, 32), (20, 33), (22, 32), (22, 33), (23, 32), (23, 25), (23, 27), (23, 29),
        (23, 33), (24, 25), (24, 27), (24, 31), (25, 31), (26, 33), (26, 29), (27, 33),
        (28, 33), (28, 31), (29, 32), (29, 33), (30, 33), (30, 32), (31, 32), (31, 33),
        (32, 33)
    ]


class SmallWorldA(Topology):
    """Small-world network.
    Manually constructing networks based on getting the edges from
    running python's NetworkX connected_watts_strogatz_graph(n, k, p) function
    """
    nickname = u'smallworlda'
    all_edges = [(0, 32), (0, 1), (0, 2), (0, 33), (1, 2), (1, 3), (2, 3), (2, 4), (3, 4), (3, 5), (4, 13), (4, 15), (5, 6), (5, 7), (6, 8), (6, 7), (7, 8), (7, 9), (8, 10), (8, 21), (9, 10), (9, 11), (10, 11), (10, 12), (11, 12), (11, 13), (12, 13), (12, 14), (13, 14), (13, 15), (14, 16), (14, 15), (15, 16), (15, 17), (15, 24), (16, 17), (16, 18), (17, 18), (17, 19), (18, 19), (18, 20), (19, 20), (19, 21), (20, 21), (20, 22), (21, 22), (21, 23), (22, 24), (22, 23), (23, 24), (23, 25), (24, 26), (25, 26), (25, 27), (26, 27), (26, 28), (27, 28), (27, 29), (27, 33), (28, 29), (28, 30), (29, 30), (29, 31), (30, 32), (30, 31), (31, 32), (31, 33), (32, 33)]

class SmallWorldB(Topology):
    nickname = u'smallworldb'
    all_edges = [(0, 32), (0, 1), (0, 2), (0, 33), (1, 33), (1, 2), (1, 3), (1, 28), (2, 3), (2, 4), (3, 4), (3, 5), (4, 24), (4, 5), (4, 6), (5, 6), (5, 22), (5, 25), (6, 8), (6, 7), (7, 8), (7, 9), (7, 27), (8, 9), (8, 10), (9, 10), (9, 11), (10, 11), (10, 12), (11, 12), (11, 13), (12, 13), (12, 14), (13, 14), (13, 15), (14, 16), (14, 15), (15, 16), (15, 17), (16, 17), (16, 18), (16, 23), (17, 18), (17, 19), (18, 19), (18, 20), (19, 20), (19, 21), (20, 21), (20, 22), (21, 22), (21, 23), (22, 24), (23, 24), (24, 25), (25, 26), (25, 27), (26, 27), (26, 28), (27, 28), (28, 30), (29, 30), (29, 31), (30, 32), (30, 31), (31, 32), (31, 33), (32, 33)]
class SmallWorldC(Topology):
    nickname = u'smallworldc'
    all_edges = [(0, 32), (0, 1), (0, 2), (0, 33), (1, 33), (1, 2), (1, 3), (2, 3), (2, 4), (3, 4), (3, 5), (4, 17), (4, 5), (4, 6), (5, 6), (5, 7), (6, 8), (6, 7), (7, 8), (7, 9), (7, 22), (8, 9), (8, 10), (9, 24), (9, 11), (10, 11), (10, 12), (11, 12), (11, 13), (12, 13), (12, 14), (13, 29), (13, 30), (13, 15), (14, 16), (14, 15), (15, 16), (15, 17), (16, 17), (16, 18), (16, 31), (17, 24), (18, 28), (18, 19), (18, 20), (19, 20), (19, 21), (19, 22), (20, 21), (20, 22), (21, 22), (21, 23), (23, 24), (23, 25), (24, 25), (24, 26), (25, 26), (25, 27), (26, 27), (26, 28), (27, 28), (27, 29), (28, 29), (29, 30), (29, 31), (30, 32), (31, 32), (32, 33)]
class SmallWorldD(Topology):
    nickname = u'smallworldd'
    all_edges = [(0, 32), (0, 1), (0, 2), (0, 13), (0, 33), (1, 33), (1, 2), (1, 3), (2, 3), (2, 5), (3, 4), (3, 5), (4, 5), (4, 6), (5, 16), (5, 32), (5, 6), (6, 8), (6, 7), (7, 8), (7, 9), (8, 9), (8, 10), (9, 10), (9, 11), (10, 11), (10, 12), (11, 12), (11, 13), (12, 13), (12, 14), (13, 15), (14, 16), (14, 15), (15, 16), (15, 17), (16, 18), (17, 18), (17, 19), (18, 19), (18, 20), (19, 20), (19, 21), (19, 31), (20, 25), (20, 21), (21, 22), (21, 23), (22, 24), (22, 23), (23, 24), (23, 27), (24, 25), (24, 26), (25, 26), (25, 27), (26, 27), (26, 28), (27, 29), (27, 31), (28, 29), (28, 30), (29, 30), (29, 31), (30, 32), (30, 31), (31, 33), (32, 33)]
class SmallWorldE(Topology):
    nickname = u'smallworlde'
    all_edges = [(0, 32), (0, 1), (0, 2), (0, 3), (0, 33), (1, 33), (1, 2), (1, 7), (2, 3), (2, 4), (3, 9), (3, 4), (4, 11), (4, 5), (4, 6), (5, 6), (5, 7), (6, 8), (6, 11), (6, 7), (7, 8), (7, 9), (8, 9), (8, 10), (9, 10), (10, 11), (10, 12), (12, 13), (12, 14), (13, 14), (13, 15), (14, 16), (14, 15), (15, 16), (15, 17), (15, 26), (16, 17), (16, 18), (17, 18), (17, 19), (18, 19), (18, 20), (19, 20), (19, 21), (20, 21), (20, 22), (21, 22), (21, 23), (22, 24), (22, 23), (23, 25), (23, 33), (24, 25), (24, 26), (25, 26), (25, 27), (26, 27), (27, 28), (27, 29), (28, 29), (28, 30), (29, 30), (29, 31), (30, 32), (30, 31), (31, 32), (31, 33), (32, 33)]
class SmallWorldF(Topology):
    nickname = u'smallworldf'
    all_edges = [(0, 32), (0, 1), (0, 2), (0, 33), (1, 33), (1, 2), (1, 3), (2, 27), (2, 4), (3, 4), (3, 5), (4, 5), (4, 6), (5, 6), (5, 7), (6, 8), (6, 7), (7, 8), (7, 9), (8, 9), (8, 10), (9, 10), (9, 11), (10, 11), (10, 12), (10, 24), (11, 12), (11, 13), (12, 13), (12, 14), (13, 14), (13, 15), (14, 16), (14, 15), (15, 16), (15, 17), (16, 17), (16, 18), (17, 18), (17, 19), (18, 19), (18, 20), (19, 20), (19, 21), (20, 21), (20, 22), (21, 22), (21, 23), (22, 27), (22, 23), (23, 24), (23, 25), (24, 26), (25, 26), (25, 27), (26, 27), (26, 28), (27, 28), (27, 29), (27, 30), (28, 29), (28, 30), (29, 30), (29, 31), (30, 31), (31, 32), (31, 33), (32, 33)]
class SmallWorldG(Topology):
    nickname = u'smallworldg'
    all_edges = [(0, 32), (0, 1), (0, 2), (0, 33), (1, 33), (1, 2), (1, 3), (2, 3), (2, 4), (2, 7), (3, 4), (3, 5), (4, 5), (4, 6), (5, 11), (5, 6), (6, 8), (6, 7), (7, 9), (8, 9), (8, 10), (9, 10), (9, 11), (10, 11), (10, 12), (10, 23), (11, 12), (11, 13), (12, 14), (12, 31), (13, 14), (13, 15), (14, 16), (14, 29), (15, 16), (15, 17), (16, 17), (16, 18), (16, 22), (17, 18), (17, 19), (18, 19), (18, 20), (19, 20), (19, 21), (20, 21), (20, 22), (21, 22), (21, 23), (22, 28), (23, 24), (24, 25), (24, 26), (25, 26), (25, 27), (26, 27), (26, 28), (26, 30), (27, 28), (27, 29), (28, 29), (28, 30), (29, 30), (29, 31), (30, 31), (31, 32), (31, 33), (32, 33)]
class SmallWorldH(Topology):
    nickname = u'smallworldh'
    all_edges = [(0, 32), (0, 2), (0, 15), (0, 33), (1, 33), (1, 2), (1, 3), (2, 3), (2, 4), (3, 5), (3, 15), (4, 17), (4, 11), (4, 5), (4, 6), (5, 18), (5, 6), (6, 10), (6, 7), (7, 8), (7, 9), (8, 10), (8, 27), (9, 10), (9, 11), (10, 20), (10, 11), (10, 12), (11, 13), (12, 13), (12, 14), (13, 18), (13, 30), (14, 16), (14, 15), (15, 16), (15, 17), (16, 17), (16, 18), (17, 18), (18, 19), (18, 20), (19, 20), (19, 21), (20, 22), (21, 22), (21, 23), (22, 24), (22, 23), (23, 24), (23, 25), (23, 27), (24, 25), (24, 26), (25, 26), (25, 27), (26, 27), (26, 28), (27, 29), (28, 29), (28, 30), (29, 30), (29, 31), (30, 32), (30, 31), (31, 32), (31, 33), (32, 33)]
class SmallWorldI(Topology):
    nickname = u'smallworldi'
    all_edges = [(0, 32), (0, 1), (0, 2), (0, 7), (0, 33), (1, 33), (1, 2), (1, 3), (2, 4), (2, 25), (3, 4), (3, 20), (4, 5), (4, 6), (5, 14), (5, 7), (6, 8), (6, 7), (7, 9), (8, 9), (8, 10), (9, 10), (9, 11), (10, 11), (10, 12), (11, 12), (11, 13), (12, 13), (12, 14), (13, 24), (13, 15), (14, 16), (14, 17), (14, 15), (15, 16), (15, 17), (16, 17), (16, 18), (17, 19), (18, 20), (18, 30), (19, 20), (19, 21), (20, 21), (20, 22), (21, 22), (21, 23), (22, 24), (22, 23), (23, 24), (23, 25), (24, 25), (24, 26), (25, 26), (25, 27), (26, 27), (26, 28), (27, 28), (27, 29), (28, 30), (28, 31), (29, 30), (29, 31), (30, 32), (30, 31), (31, 32), (31, 33), (32, 33)]
class SmallWorldJ(Topology):
    nickname = u'smallworldj'
    all_edges = [(0, 32), (0, 1), (0, 2), (0, 33), (1, 33), (1, 2), (1, 3), (2, 3), (2, 4), (3, 4), (3, 5), (3, 20), (4, 5), (4, 6), (5, 6), (5, 7), (6, 8), (6, 7), (7, 8), (7, 9), (8, 9), (8, 10), (9, 10), (9, 29), (10, 11), (10, 12), (11, 12), (11, 13), (12, 13), (12, 14), (13, 14), (13, 15), (14, 16), (14, 31), (14, 30), (14, 15), (15, 17), (15, 30), (16, 17), (16, 29), (17, 18), (17, 19), (18, 19), (18, 20), (19, 20), (19, 21), (20, 21), (21, 22), (21, 23), (22, 24), (22, 23), (23, 24), (23, 25), (24, 25), (24, 26), (25, 26), (25, 27), (26, 27), (26, 28), (27, 28), (27, 29), (28, 29), (28, 30), (29, 30), (29, 31), (30, 32), (31, 33), (32, 33)]
class SmallWorldK(Topology):
    nickname = u'smallworldk'
    all_edges = [(0, 1), (0, 2), (0, 31), (0, 33), (1, 33), (1, 3), (1, 27), (2, 3), (2, 4), (3, 4), (3, 5), (4, 5), (4, 6), (5, 21), (5, 6), (5, 7), (6, 8), (6, 7), (7, 8), (7, 9), (8, 9), (8, 10), (9, 10), (9, 11), (10, 11), (10, 12), (11, 12), (11, 13), (12, 13), (12, 14), (13, 14), (13, 15), (14, 16), (14, 15), (15, 16), (15, 17), (16, 18), (16, 26), (17, 18), (17, 19), (18, 19), (18, 20), (19, 20), (19, 21), (20, 21), (20, 22), (21, 32), (21, 22), (22, 24), (22, 23), (23, 24), (23, 25), (24, 25), (24, 26), (25, 26), (25, 27), (26, 27), (26, 28), (27, 28), (27, 29), (28, 29), (28, 30), (29, 30), (29, 31), (30, 32), (30, 31), (31, 33), (32, 33)]
class SmallWorldL(Topology):
    nickname = u'smallworldl'
    all_edges = [(0, 32), (0, 1), (0, 2), (0, 33), (1, 33), (1, 2), (1, 3), (2, 3), (2, 4), (3, 4), (3, 23), (3, 7), (4, 5), (4, 6), (5, 6), (5, 7), (6, 8), (6, 7), (7, 8), (7, 28), (8, 10), (8, 11), (9, 10), (9, 11), (9, 15), (10, 11), (10, 12), (11, 12), (11, 13), (12, 13), (12, 14), (13, 14), (13, 15), (14, 16), (14, 21), (14, 26), (14, 15), (15, 16), (16, 17), (16, 18), (17, 18), (17, 19), (17, 20), (18, 19), (18, 20), (19, 20), (19, 21), (20, 28), (21, 23), (22, 24), (22, 23), (23, 24), (23, 25), (24, 25), (24, 26), (25, 26), (25, 27), (26, 28), (27, 28), (27, 29), (28, 29), (29, 30), (29, 31), (30, 32), (30, 31), (31, 32), (31, 33), (32, 33)]
class SmallWorldM(Topology):
    nickname = u'smallworldm'
    all_edges = [(0, 32), (0, 1), (0, 2), (0, 33), (1, 33), (1, 2), (1, 3), (1, 18), (2, 3), (2, 4), (3, 4), (3, 5), (3, 28), (4, 5), (4, 6), (5, 6), (5, 7), (6, 8), (6, 7), (7, 8), (7, 9), (7, 11), (8, 9), (8, 10), (9, 10), (9, 11), (10, 11), (10, 12), (11, 13), (12, 13), (12, 14), (13, 14), (13, 15), (14, 16), (14, 23), (14, 15), (15, 16), (15, 17), (16, 17), (16, 18), (17, 18), (17, 19), (18, 20), (19, 20), (19, 21), (20, 21), (20, 22), (21, 22), (21, 23), (22, 25), (22, 23), (23, 25), (24, 25), (24, 26), (25, 26), (25, 27), (26, 27), (26, 28), (27, 28), (27, 29), (28, 30), (28, 31), (29, 30), (29, 31), (30, 32), (30, 31), (31, 33), (32, 33)]
class SmallWorldN(Topology):
    nickname = u'smallworldn'
    all_edges = [(0, 1), (0, 2), (0, 33), (1, 33), (1, 2), (1, 3), (2, 4), (2, 13), (3, 4), (3, 5), (4, 33), (4, 11), (5, 6), (5, 7), (6, 8), (6, 23), (7, 8), (7, 9), (7, 18), (8, 9), (8, 10), (9, 23), (9, 10), (9, 11), (10, 11), (10, 12), (11, 12), (11, 13), (12, 13), (12, 14), (13, 14), (13, 15), (14, 16), (14, 15), (15, 16), (15, 17), (16, 17), (16, 18), (17, 18), (17, 19), (18, 19), (19, 32), (19, 20), (19, 21), (20, 21), (20, 22), (21, 22), (21, 23), (22, 24), (22, 23), (23, 24), (24, 25), (24, 26), (25, 27), (25, 28), (26, 27), (26, 28), (27, 28), (27, 29), (28, 29), (28, 30), (29, 30), (29, 31), (30, 32), (30, 31), (31, 32), (31, 33), (32, 33)]
class SmallWorldO(Topology):
    nickname = u'smallworldo'
    all_edges = [(0, 32), (0, 1), (0, 2), (0, 33), (1, 33), (1, 2), (1, 3), (1, 18), (2, 3), (2, 4), (3, 4), (3, 5), (4, 5), (4, 6), (5, 6), (5, 7), (6, 8), (6, 7), (7, 8), (7, 9), (8, 9), (8, 10), (9, 10), (9, 11), (10, 11), (10, 12), (11, 12), (11, 13), (12, 13), (12, 14), (13, 14), (13, 15), (14, 16), (14, 15), (15, 16), (15, 17), (16, 17), (16, 18), (17, 18), (17, 19), (17, 29), (18, 19), (19, 20), (19, 21), (20, 21), (20, 22), (21, 22), (21, 23), (22, 24), (22, 23), (23, 24), (23, 32), (24, 25), (24, 26), (25, 26), (25, 27), (26, 27), (26, 28), (27, 28), (27, 29), (28, 29), (28, 30), (29, 30), (30, 32), (30, 31), (31, 32), (31, 33), (32, 33)]
class SmallWorldP(Topology):
    nickname = u'smallworldp'
    all_edges = [(0, 32), (0, 1), (0, 2), (0, 33), (1, 33), (1, 2), (1, 3), (2, 3), (2, 4), (3, 4), (3, 5), (4, 5), (4, 6), (5, 15), (5, 7), (6, 17), (6, 7), (7, 27), (7, 12), (8, 9), (8, 10), (9, 10), (9, 11), (10, 11), (10, 12), (11, 12), (11, 13), (12, 13), (12, 14), (13, 14), (13, 15), (14, 16), (14, 15), (15, 16), (15, 17), (16, 17), (16, 18), (17, 18), (17, 19), (18, 19), (18, 20), (19, 20), (19, 21), (20, 21), (20, 22), (21, 22), (21, 23), (22, 24), (22, 23), (23, 24), (23, 25), (24, 25), (24, 26), (25, 26), (25, 27), (26, 27), (26, 28), (27, 28), (27, 29), (28, 29), (28, 30), (29, 30), (29, 31), (30, 32), (30, 31), (31, 32), (31, 33), (32, 33)]


def _descendent_classes(cls):
    for cls in cls.__subclasses__():
        yield cls
        for cls in _descendent_classes(cls):
            yield cls


BY_NAME = {}
for cls in _descendent_classes(Topology):
    BY_NAME[cls.__name__] = BY_NAME[cls.nickname] = cls


def by_name(name):
    """Attempt to return a Topology subclass by name.

    Actual class names and known nicknames are both supported.
    """
    klass = BY_NAME.get(name)
    if klass is not None:
        return klass()

# old:

# FULLY CONNECTED:
# 2 subjects
# all_edges = [(0, 1)]
# 4 subjects
# all_edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
# 8 subjects
# all_edges = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (3, 4), (3, 5), (3, 6), (3, 7), (4, 5), (4, 6), (4, 7), (5, 6), (5, 7), (6, 7)]
# 16 subjects
# all_edges = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (0, 9), (0, 10), (0, 11), (0, 12), (0, 13), (0, 14), (0, 15), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11), (1, 12), (1, 13), (1, 14), (1, 15), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (2, 10), (2, 11), (2, 12), (2, 13), (2, 14), (2, 15), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9), (3, 10), (3, 11), (3, 12), (3, 13), (3, 14), (3, 15), (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 10), (4, 11), (4, 12), (4, 13), (4, 14), (4, 15), (5, 6), (5, 7), (5, 8), (5, 9), (5, 10), (5, 11), (5, 12), (5, 13), (5, 14), (5, 15), (6, 7), (6, 8), (6, 9), (6, 10), (6, 11), (6, 12), (6, 13), (6, 14), (6, 15), (7, 8), (7, 9), (7, 10), (7, 11), (7, 12), (7, 13), (7, 14), (7, 15), (8, 9), (8, 10), (8, 11), (8, 12), (8, 13), (8, 14), (8, 15), (9, 10), (9, 11), (9, 12), (9, 13), (9, 14), (9, 15), (10, 11), (10, 12), (10, 13), (10, 14), (10, 15), (11, 12), (11, 13), (11, 14), (11, 15), (12, 13), (12, 14), (12, 15), (13, 14), (13, 15), (14, 15)]
# 32 subjects
# all_edges = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (0, 9), (0, 10), (0, 11), (0, 12), (0, 13), (0, 14), (0, 15), (0, 16), (0, 17), (0, 18), (0, 19), (0, 20), (0, 21), (0, 22), (0, 23), (0, 24), (0, 25), (0, 26), (0, 27), (0, 28), (0, 29), (0, 30), (0, 31), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11), (1, 12), (1, 13), (1, 14), (1, 15), (1, 16), (1, 17), (1, 18), (1, 19), (1, 20), (1, 21), (1, 22), (1, 23), (1, 24), (1, 25), (1, 26), (1, 27), (1, 28), (1, 29), (1, 30), (1, 31), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (2, 10), (2, 11), (2, 12), (2, 13), (2, 14), (2, 15), (2, 16), (2, 17), (2, 18), (2, 19), (2, 20), (2, 21), (2, 22), (2, 23), (2, 24), (2, 25), (2, 26), (2, 27), (2, 28), (2, 29), (2, 30), (2, 31), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9), (3, 10), (3, 11), (3, 12), (3, 13), (3, 14), (3, 15), (3, 16), (3, 17), (3, 18), (3, 19), (3, 20), (3, 21), (3, 22), (3, 23), (3, 24), (3, 25), (3, 26), (3, 27), (3, 28), (3, 29), (3, 30), (3, 31), (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 10), (4, 11), (4, 12), (4, 13), (4, 14), (4, 15), (4, 16), (4, 17), (4, 18), (4, 19), (4, 20), (4, 21), (4, 22), (4, 23), (4, 24), (4, 25), (4, 26), (4, 27), (4, 28), (4, 29), (4, 30), (4, 31), (5, 6), (5, 7), (5, 8), (5, 9), (5, 10), (5, 11), (5, 12), (5, 13), (5, 14), (5, 15), (5, 16), (5, 17), (5, 18), (5, 19), (5, 20), (5, 21), (5, 22), (5, 23), (5, 24), (5, 25), (5, 26), (5, 27), (5, 28), (5, 29), (5, 30), (5, 31), (6, 7), (6, 8), (6, 9), (6, 10), (6, 11), (6, 12), (6, 13), (6, 14), (6, 15), (6, 16), (6, 17), (6, 18), (6, 19), (6, 20), (6, 21), (6, 22), (6, 23), (6, 24), (6, 25), (6, 26), (6, 27), (6, 28), (6, 29), (6, 30), (6, 31), (7, 8), (7, 9), (7, 10), (7, 11), (7, 12), (7, 13), (7, 14), (7, 15), (7, 16), (7, 17), (7, 18), (7, 19), (7, 20), (7, 21), (7, 22), (7, 23), (7, 24), (7, 25), (7, 26), (7, 27), (7, 28), (7, 29), (7, 30), (7, 31), (8, 9), (8, 10), (8, 11), (8, 12), (8, 13), (8, 14), (8, 15), (8, 16), (8, 17), (8, 18), (8, 19), (8, 20), (8, 21), (8, 22), (8, 23), (8, 24), (8, 25), (8, 26), (8, 27), (8, 28), (8, 29), (8, 30), (8, 31), (9, 10), (9, 11), (9, 12), (9, 13), (9, 14), (9, 15), (9, 16), (9, 17), (9, 18), (9, 19), (9, 20), (9, 21), (9, 22), (9, 23), (9, 24), (9, 25), (9, 26), (9, 27), (9, 28), (9, 29), (9, 30), (9, 31), (10, 11), (10, 12), (10, 13), (10, 14), (10, 15), (10, 16), (10, 17), (10, 18), (10, 19), (10, 20), (10, 21), (10, 22), (10, 23), (10, 24), (10, 25), (10, 26), (10, 27), (10, 28), (10, 29), (10, 30), (10, 31), (11, 12), (11, 13), (11, 14), (11, 15), (11, 16), (11, 17), (11, 18), (11, 19), (11, 20), (11, 21), (11, 22), (11, 23), (11, 24), (11, 25), (11, 26), (11, 27), (11, 28), (11, 29), (11, 30), (11, 31), (12, 13), (12, 14), (12, 15), (12, 16), (12, 17), (12, 18), (12, 19), (12, 20), (12, 21), (12, 22), (12, 23), (12, 24), (12, 25), (12, 26), (12, 27), (12, 28), (12, 29), (12, 30), (12, 31), (13, 14), (13, 15), (13, 16), (13, 17), (13, 18), (13, 19), (13, 20), (13, 21), (13, 22), (13, 23), (13, 24), (13, 25), (13, 26), (13, 27), (13, 28), (13, 29), (13, 30), (13, 31), (14, 15), (14, 16), (14, 17), (14, 18), (14, 19), (14, 20), (14, 21), (14, 22), (14, 23), (14, 24), (14, 25), (14, 26), (14, 27), (14, 28), (14, 29), (14, 30), (14, 31), (15, 16), (15, 17), (15, 18), (15, 19), (15, 20), (15, 21), (15, 22), (15, 23), (15, 24), (15, 25), (15, 26), (15, 27), (15, 28), (15, 29), (15, 30), (15, 31), (16, 17), (16, 18), (16, 19), (16, 20), (16, 21), (16, 22), (16, 23), (16, 24), (16, 25), (16, 26), (16, 27), (16, 28), (16, 29), (16, 30), (16, 31), (17, 18), (17, 19), (17, 20), (17, 21), (17, 22), (17, 23), (17, 24), (17, 25), (17, 26), (17, 27), (17, 28), (17, 29), (17, 30), (17, 31), (18, 19), (18, 20), (18, 21), (18, 22), (18, 23), (18, 24), (18, 25), (18, 26), (18, 27), (18, 28), (18, 29), (18, 30), (18, 31), (19, 20), (19, 21), (19, 22), (19, 23), (19, 24), (19, 25), (19, 26), (19, 27), (19, 28), (19, 29), (19, 30), (19, 31), (20, 21), (20, 22), (20, 23), (20, 24), (20, 25), (20, 26), (20, 27), (20, 28), (20, 29), (20, 30), (20, 31), (21, 22), (21, 23), (21, 24), (21, 25), (21, 26), (21, 27), (21, 28), (21, 29), (21, 30), (21, 31), (22, 23), (22, 24), (22, 25), (22, 26), (22, 27), (22, 28), (22, 29), (22, 30), (22, 31), (23, 24), (23, 25), (23, 26), (23, 27), (23, 28), (23, 29), (23, 30), (23, 31), (24, 25), (24, 26), (24, 27), (24, 28), (24, 29), (24, 30), (24, 31), (25, 26), (25, 27), (25, 28), (25, 29), (25, 30), (25, 31), (26, 27), (26, 28), (26, 29), (26, 30), (26, 31), (27, 28), (27, 29), (27, 30), (27, 31), (28, 29), (28, 30), (28, 31), (29, 30), (29, 31), (30, 31)]
# 34 subjects
# all_edges = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (0, 9), (0, 10), (0, 11), (0, 12), (0, 13), (0, 14), (0, 15), (0, 16), (0, 17), (0, 18), (0, 19), (0, 20), (0, 21), (0, 22), (0, 23), (0, 24), (0, 25), (0, 26), (0, 27), (0, 28), (0, 29), (0, 30), (0, 31), (0, 32), (0, 33), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11), (1, 12), (1, 13), (1, 14), (1, 15), (1, 16), (1, 17), (1, 18), (1, 19), (1, 20), (1, 21), (1, 22), (1, 23), (1, 24), (1, 25), (1, 26), (1, 27), (1, 28), (1, 29), (1, 30), (1, 31), (1, 32), (1, 33), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (2, 10), (2, 11), (2, 12), (2, 13), (2, 14), (2, 15), (2, 16), (2, 17), (2, 18), (2, 19), (2, 20), (2, 21), (2, 22), (2, 23), (2, 24), (2, 25), (2, 26), (2, 27), (2, 28), (2, 29), (2, 30), (2, 31), (2, 32), (2, 33), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9), (3, 10), (3, 11), (3, 12), (3, 13), (3, 14), (3, 15), (3, 16), (3, 17), (3, 18), (3, 19), (3, 20), (3, 21), (3, 22), (3, 23), (3, 24), (3, 25), (3, 26), (3, 27), (3, 28), (3, 29), (3, 30), (3, 31), (3, 32), (3, 33), (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 10), (4, 11), (4, 12), (4, 13), (4, 14), (4, 15), (4, 16), (4, 17), (4, 18), (4, 19), (4, 20), (4, 21), (4, 22), (4, 23), (4, 24), (4, 25), (4, 26), (4, 27), (4, 28), (4, 29), (4, 30), (4, 31), (4, 32), (4, 33), (5, 6), (5, 7), (5, 8), (5, 9), (5, 10), (5, 11), (5, 12), (5, 13), (5, 14), (5, 15), (5, 16), (5, 17), (5, 18), (5, 19), (5, 20), (5, 21), (5, 22), (5, 23), (5, 24), (5, 25), (5, 26), (5, 27), (5, 28), (5, 29), (5, 30), (5, 31), (5, 32), (5, 33), (6, 7), (6, 8), (6, 9), (6, 10), (6, 11), (6, 12), (6, 13), (6, 14), (6, 15), (6, 16), (6, 17), (6, 18), (6, 19), (6, 20), (6, 21), (6, 22), (6, 23), (6, 24), (6, 25), (6, 26), (6, 27), (6, 28), (6, 29), (6, 30), (6, 31), (6, 32), (6, 33), (7, 8), (7, 9), (7, 10), (7, 11), (7, 12), (7, 13), (7, 14), (7, 15), (7, 16), (7, 17), (7, 18), (7, 19), (7, 20), (7, 21), (7, 22), (7, 23), (7, 24), (7, 25), (7, 26), (7, 27), (7, 28), (7, 29), (7, 30), (7, 31), (7, 32), (7, 33), (8, 9), (8, 10), (8, 11), (8, 12), (8, 13), (8, 14), (8, 15), (8, 16), (8, 17), (8, 18), (8, 19), (8, 20), (8, 21), (8, 22), (8, 23), (8, 24), (8, 25), (8, 26), (8, 27), (8, 28), (8, 29), (8, 30), (8, 31), (8, 32), (8, 33), (9, 10), (9, 11), (9, 12), (9, 13), (9, 14), (9, 15), (9, 16), (9, 17), (9, 18), (9, 19), (9, 20), (9, 21), (9, 22), (9, 23), (9, 24), (9, 25), (9, 26), (9, 27), (9, 28), (9, 29), (9, 30), (9, 31), (9, 32), (9, 33), (10, 11), (10, 12), (10, 13), (10, 14), (10, 15), (10, 16), (10, 17), (10, 18), (10, 19), (10, 20), (10, 21), (10, 22), (10, 23), (10, 24), (10, 25), (10, 26), (10, 27), (10, 28), (10, 29), (10, 30), (10, 31), (10, 32), (10, 33), (11, 12), (11, 13), (11, 14), (11, 15), (11, 16), (11, 17), (11, 18), (11, 19), (11, 20), (11, 21), (11, 22), (11, 23), (11, 24), (11, 25), (11, 26), (11, 27), (11, 28), (11, 29), (11, 30), (11, 31), (11, 32), (11, 33), (12, 13), (12, 14), (12, 15), (12, 16), (12, 17), (12, 18), (12, 19), (12, 20), (12, 21), (12, 22), (12, 23), (12, 24), (12, 25), (12, 26), (12, 27), (12, 28), (12, 29), (12, 30), (12, 31), (12, 32), (12, 33), (13, 14), (13, 15), (13, 16), (13, 17), (13, 18), (13, 19), (13, 20), (13, 21), (13, 22), (13, 23), (13, 24), (13, 25), (13, 26), (13, 27), (13, 28), (13, 29), (13, 30), (13, 31), (13, 32), (13, 33), (14, 15), (14, 16), (14, 17), (14, 18), (14, 19), (14, 20), (14, 21), (14, 22), (14, 23), (14, 24), (14, 25), (14, 26), (14, 27), (14, 28), (14, 29), (14, 30), (14, 31), (14, 32), (14, 33), (15, 16), (15, 17), (15, 18), (15, 19), (15, 20), (15, 21), (15, 22), (15, 23), (15, 24), (15, 25), (15, 26), (15, 27), (15, 28), (15, 29), (15, 30), (15, 31), (15, 32), (15, 33), (16, 17), (16, 18), (16, 19), (16, 20), (16, 21), (16, 22), (16, 23), (16, 24), (16, 25), (16, 26), (16, 27), (16, 28), (16, 29), (16, 30), (16, 31), (16, 32), (16, 33), (17, 18), (17, 19), (17, 20), (17, 21), (17, 22), (17, 23), (17, 24), (17, 25), (17, 26), (17, 27), (17, 28), (17, 29), (17, 30), (17, 31), (17, 32), (17, 33), (18, 19), (18, 20), (18, 21), (18, 22), (18, 23), (18, 24), (18, 25), (18, 26), (18, 27), (18, 28), (18, 29), (18, 30), (18, 31), (18, 32), (18, 33), (19, 20), (19, 21), (19, 22), (19, 23), (19, 24), (19, 25), (19, 26), (19, 27), (19, 28), (19, 29), (19, 30), (19, 31), (19, 32), (19, 33), (20, 21), (20, 22), (20, 23), (20, 24), (20, 25), (20, 26), (20, 27), (20, 28), (20, 29), (20, 30), (20, 31), (20, 32), (20, 33), (21, 22), (21, 23), (21, 24), (21, 25), (21, 26), (21, 27), (21, 28), (21, 29), (21, 30), (21, 31), (21, 32), (21, 33), (22, 23), (22, 24), (22, 25), (22, 26), (22, 27), (22, 28), (22, 29), (22, 30), (22, 31), (22, 32), (22, 33), (23, 24), (23, 25), (23, 26), (23, 27), (23, 28), (23, 29), (23, 30), (23, 31), (23, 32), (23, 33), (24, 25), (24, 26), (24, 27), (24, 28), (24, 29), (24, 30), (24, 31), (24, 32), (24, 33), (25, 26), (25, 27), (25, 28), (25, 29), (25, 30), (25, 31), (25, 32), (25, 33), (26, 27), (26, 28), (26, 29), (26, 30), (26, 31), (26, 32), (26, 33), (27, 28), (27, 29), (27, 30), (27, 31), (27, 32), (27, 33), (28, 29), (28, 30), (28, 31), (28, 32), (28, 33), (29, 30), (29, 31), (29, 32), (29, 33), (30, 31), (30, 32), (30, 33), (31, 32), (31, 33), (32, 33)]

# 2s
# all_edges = [(0,1),(2,3),(4,5),(6,7),(8,9),
# (10,11),(12,13),(14,15),(16,17),(18,19),(20,21),
# (22,23),(24,25),(26,27),(28,29),(30,31),(32,33),
# (34,35),(36,37),(38,39),(40,41),(42,43)]

# 3s
# all_edges = [(0,1),(0,2),(1,2),
# (3,4),(3,5),(4,5),
# (6,7),(6,8),(7,8),
# (9,10),(9,11),(10,11),
# (12,13),(12,14),(13,14),
# (15,16),(15,17),(16,17),
# (18,19),(18,20),(19,20),
# (21,22),(21,23),(22,23),
# (24,25),(24,26),(25,26),
# (27,28),(27,29),(28,29),
# (30,31),(30,32),(31,32),
# (33,34),(33,35),(34,35),
# (36,37),(36,38),(37,38)]

# 4s
# all_edges =  [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3),
# (4,5),(4,6),(4,7),(5,6),(5,7),(6,7),
# (8,9),(8,10),(8,11),(9,10),(9,11),(10,11),
# (12,13),(12,14),(12,15),(13,14),(13,15),(14,15),
# (16,17),(16,18),(16,19),(17,18),(17,19),(18,19),
# (20,21),(20,22),(20,23),(21,22),(21,23),(22,23),
# (24,25),(24,26),(24,27),(25,26),(25,27),(26,27),
# (28,29),(28,30),(28,31),(29,30),(29,31),(30,31),
# (32,33),(32,34),(32,35),(33,34),(33,35),(34,35),
# (36,37),(36,38),(36,39),(37,38),(37,39),(38,39),
# (40,41),(40,42),(40,43),(41,42),(41,43),(42,43),
# (44,45),(44,46),(44,47),(45,46),(45,47),(46,47),
# (48,49),(48,50),(48,51),(49,50),(49,51),(50,51),
# (52,53),(52,54),(52,55),(53,54),(53,55),(54,55),
# (56,57),(56,58),(56,59),(57,58),(57,59),(58,59)]