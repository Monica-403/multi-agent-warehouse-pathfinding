"""
algorithms/constraints.py
Vertex and edge constraints used by CBS to restrict Space-Time A*.
"""

from dataclasses import dataclass
from typing import Tuple

Position = Tuple[int, int]


@dataclass(frozen=True)
class VertexConstraint:
    """Robot `agent` cannot occupy `position` at time `time`."""
    agent: int
    position: Position
    time: int


@dataclass(frozen=True)
class EdgeConstraint:
    """Robot `agent` cannot move from `pos_from` to `pos_to` at time `time` (arriving at time+1)."""
    agent: int
    pos_from: Position
    pos_to: Position
    time: int


class ConstraintSet:
    """Holds all constraints for a single CBS node."""

    def __init__(self):
        self.vertex_constraints = set()
        self.edge_constraints = set()

    def copy(self):
        new = ConstraintSet()
        new.vertex_constraints = set(self.vertex_constraints)
        new.edge_constraints = set(self.edge_constraints)
        return new

    def add_vertex_constraint(self, c: VertexConstraint):
        self.vertex_constraints.add(c)

    def add_edge_constraint(self, c: EdgeConstraint):
        self.edge_constraints.add(c)

    def is_vertex_blocked(self, agent: int, pos: Position, time: int) -> bool:
        return VertexConstraint(agent, pos, time) in self.vertex_constraints

    def is_edge_blocked(self, agent: int, pos_from: Position, pos_to: Position, time: int) -> bool:
        return EdgeConstraint(agent, pos_from, pos_to, time) in self.edge_constraints

    def for_agent(self, agent: int):
        """Return the subset of constraints relevant to one agent (for fast lookup)."""
        v = {c for c in self.vertex_constraints if c.agent == agent}
        e = {c for c in self.edge_constraints if c.agent == agent}
        return v, e