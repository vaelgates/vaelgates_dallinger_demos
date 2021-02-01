from dallinger import nodes
from dallinger import models


class Query(object):

    def index_of(self, node):
        """Return the index/creation order offset of the given Node.
        """
        agents = nodes.Agent.query.all()
        node_index = agents.index(node)
        return node_index

    def partner_indexes(self, node):
        """Return a list of Agent indexes (based on creation order)
        for the neighbors of the provided Agent/Node.
        """
        agents = nodes.Agent.query.all()
        node_index = agents.index(node)
        neighbors = agents[node_index].neighbors()
        return [agents.index(n) for n in neighbors]

    def agent_index_vectors(self):
        agents = self._agents()
        vectors = self._vectors()

        result = [
            (agents.index(v.origin), agents.index(v.destination))
            for v in vectors
        ]

        return sorted(result)

    def unique_agent_index_vectors(self):
        agents = self._agents()
        vectors = self._vectors()
        unique_pairs = set()
        for v in vectors:
            ordered = tuple(
                sorted([agents.index(v.origin), agents.index(v.destination)])
            )
            unique_pairs.add(ordered)

        return sorted(list(unique_pairs))

    def _agents(self):
        return nodes.Agent.query.all()

    def _vectors(self):
        vectors = [
            v for v in models.Vector.query.all()
            if v.origin.participant_id is not None
        ]
        return vectors
