import random


class Transmitter(object):
    """Abastract base class"""

    nickname = None

    def transmit(self, node, info):
        raise NotImplementedError("Transmitter is abstract.")


class AllNeighbors(Transmitter):
    """Transmit to every neighbor of the source Node."""

    nickname = u'promiscuous'

    def transmit(self, node, info):
        recipients = [node.participant_id]
        for agent in node.neighbors():
            node.transmit(what=info, to_whom=agent)
            recipients.append(agent.participant_id)

        return recipients


class SingleRandomNeighbor(Transmitter):
    """Transfer info to only one neighbor, selected at random."""

    nickname = u'random'

    def transmit(self, node, info):
        agent = random.choice(node.neighbors())
        node.transmit(what=info, to_whom=agent)
        recipients = [node.participant_id, agent.participant_id]

        return recipients


def _descendent_classes(cls):
    for cls in cls.__subclasses__():
        yield cls
        for cls in _descendent_classes(cls):
            yield cls


BY_NAME = {}
for cls in _descendent_classes(Transmitter):
    BY_NAME[cls.__name__] = BY_NAME[cls.nickname] = cls


def by_name(name):
    """Attempt to return a Transmitter class by name.

    Actual class names and known nicknames are both supported.
    """
    klass = BY_NAME.get(name)
    if klass is not None:
        return klass()
