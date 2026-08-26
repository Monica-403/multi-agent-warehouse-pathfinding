"""
environment/robot.py
Robot data model.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional

Position = Tuple[int, int]
PathState = Tuple[int, int, int]  # (x, y, t)


@dataclass
class Robot:
    id: int
    start: Position
    goal: Position
    path: Optional[List[PathState]] = field(default=None)

    def path_cost(self) -> int:
        """Number of moves (path length - 1). Returns -1 if no path."""
        if not self.path:
            return -1
        return len(self.path) - 1

    def finish_time(self) -> int:
        if not self.path:
            return -1
        return self.path[-1][2]

    def position_at(self, t: int) -> Position:
        """Get robot's position at time t (stays at goal if t exceeds path length)."""
        if not self.path:
            return self.start
        if t < 0:
            return self.start
        if t >= len(self.path):
            return self.path[-1][0], self.path[-1][1]
        return self.path[t][0], self.path[t][1]

    def __repr__(self):
        return f"Robot(id={self.id}, start={self.start}, goal={self.goal})"