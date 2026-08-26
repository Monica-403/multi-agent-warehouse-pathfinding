"""
algorithms/conflict.py
Detects vertex and edge conflicts between planned robot paths.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

Position = Tuple[int, int]
PathState = Tuple[int, int, int]


@dataclass
class Conflict:
    type: str  # "vertex" or "edge"
    agent_a: int
    agent_b: int
    position_a: Position
    position_b: Position
    time: int


def _position_at(path: List[PathState], t: int) -> Position:
    """Position of a robot at time t. Robots wait at their goal after finishing."""
    if t < path[0][2]:
        return path[0][0], path[0][1]
    if t >= path[-1][2]:
        return path[-1][0], path[-1][1]
    return path[t][0], path[t][1]


def find_first_conflict(paths: Dict[int, List[PathState]]) -> Optional[Conflict]:
    """
    Scans all pairs of robot paths and returns the first conflict found
    (vertex or edge), or None if the set of paths is collision-free.
    """
    agent_ids = list(paths.keys())
    max_t = max(path[-1][2] for path in paths.values())

    for t in range(max_t + 1):
        # Vertex conflicts: two robots in the same cell at the same time
        positions_at_t = {}
        for agent in agent_ids:
            pos = _position_at(paths[agent], t)
            if pos in positions_at_t:
                other_agent = positions_at_t[pos]
                return Conflict("vertex", other_agent, agent, pos, pos, t)
            positions_at_t[pos] = agent

        # Edge conflicts: two robots swap cells between t and t+1
        if t < max_t:
            for i in range(len(agent_ids)):
                for j in range(i + 1, len(agent_ids)):
                    a, b = agent_ids[i], agent_ids[j]
                    a_now, a_next = _position_at(paths[a], t), _position_at(paths[a], t + 1)
                    b_now, b_next = _position_at(paths[b], t), _position_at(paths[b], t + 1)
                    if a_now == b_next and a_next == b_now and a_now != a_next:
                        return Conflict("edge", a, b, a_now, a_next, t)

    return None