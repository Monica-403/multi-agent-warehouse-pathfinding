"""
environment/grid.py
Grid representation of the warehouse: free cells, obstacles, and neighbor logic.
"""

from typing import List, Tuple, Set

Position = Tuple[int, int]


class Grid:
    def __init__(self, grid_data: List[List[int]]):
        """
        grid_data: 2D list, 0 = free cell, 1 = obstacle
        """
        self.data = grid_data
        self.height = len(grid_data)
        self.width = len(grid_data[0]) if self.height > 0 else 0

    def in_bounds(self, pos: Position) -> bool:
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def is_free(self, pos: Position) -> bool:
        x, y = pos
        return self.data[y][x] == 0

    def is_valid(self, pos: Position) -> bool:
        return self.in_bounds(pos) and self.is_free(pos)

    def neighbors(self, pos: Position) -> List[Position]:
        """4-connected movement: UP, DOWN, LEFT, RIGHT (no diagonals)."""
        x, y = pos
        candidates = [
            (x + 1, y),  # RIGHT
            (x - 1, y),  # LEFT
            (x, y + 1),  # DOWN
            (x, y - 1),  # UP
        ]
        return [c for c in candidates if self.is_valid(c)]

    @classmethod
    def from_dimensions(cls, width: int, height: int, obstacles: Set[Position] = None):
        obstacles = obstacles or set()
        data = [[1 if (x, y) in obstacles else 0 for x in range(width)] for y in range(height)]
        return cls(data)

    def __repr__(self):
        rows = []
        for row in self.data:
            rows.append(" ".join(str(c) for c in row))
        return "\n".join(rows)