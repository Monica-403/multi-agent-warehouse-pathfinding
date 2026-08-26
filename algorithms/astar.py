"""
algorithms/astar.py
Standard A* pathfinding (no time dimension). Used as a warm-up / building block
before Space-Time A*.
"""

import heapq
from typing import List, Optional, Tuple
from environment.grid import Grid

Position = Tuple[int, int]


def manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid: Grid, start: Position, goal: Position) -> Optional[List[Position]]:
    open_set = []
    heapq.heappush(open_set, (manhattan(start, goal), 0, start))
    came_from = {}
    g_score = {start: 0}
    visited = set()

    while open_set:
        _, cost, current = heapq.heappop(open_set)

        if current == goal:
            return _reconstruct(came_from, current)

        if current in visited:
            continue
        visited.add(current)

        for neighbor in grid.neighbors(current):
            tentative_g = cost + 1
            if tentative_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = tentative_g
                f = tentative_g + manhattan(neighbor, goal)
                heapq.heappush(open_set, (f, tentative_g, neighbor))
                came_from[neighbor] = current

    return None  # No path found


def _reconstruct(came_from, current) -> List[Position]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path