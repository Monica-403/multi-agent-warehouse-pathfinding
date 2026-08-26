"""
tests/test_astar.py
Tests for the basic A* pathfinder (no time dimension).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from environment.grid import Grid
from algorithms.astar import astar


def test_simple_path_found():
    grid = Grid([
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ])
    path = astar(grid, (0, 0), (2, 2))
    assert path is not None
    assert path[0] == (0, 0)
    assert path[-1] == (2, 2)


def test_path_avoids_obstacles():
    grid = Grid([
        [0, 1, 0],
        [0, 1, 0],
        [0, 0, 0],
    ])
    path = astar(grid, (0, 0), (2, 0))
    assert path is not None
    for (x, y) in path:
        assert grid.data[y][x] == 0  # never steps on an obstacle


def test_unreachable_goal_returns_none():
    grid = Grid([
        [0, 1, 0],
        [1, 1, 0],
        [0, 1, 0],
    ])
    # (0,0) is sealed off from (2,0) by a wall of 1s
    path = astar(grid, (0, 0), (2, 0))
    assert path is None