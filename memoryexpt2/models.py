"""Define kinds of nodes: agents, sources, and environments."""

from dallinger.models import Info

class Fillerans(Info):
    """A fillerans"""

    __mapper_args__ = {"polymorphic_identity": "fillerans"}

