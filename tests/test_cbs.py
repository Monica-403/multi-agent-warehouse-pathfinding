"""
tests/test_cbs.py
Integration tests for the full CBS high-level search.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from environment.grid import Grid
from environment.robot import Robot
from algorithms.cbs import cbs_search
from algorithms.conflict import find_first_conflict


def test_single_robot_solves():
    grid = Grid([
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ])
    robots = [Robot(id=1, start=(0, 0), goal=(2, 2))]
    result = cbs_search(grid, robots)
    assert result.success
    assert result.paths[1][0][:2] == (0, 0)
    assert result.paths[1][-1][:2] == (2, 2)


def test_two_robots_head_on_corridor_resolved_without_collision():
    """
    Two robots moving toward each other in a corridor -- CBS must
    make one of them wait or step aside so they never swap or occupy
    the same cell at the same time. Uses a 2-row grid so there is
    room to step aside (a strict 1-wide corridor makes swapping
    mathematically impossible -- see test below).
    """
    grid = Grid([
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ])
    robots = [
        Robot(id=1, start=(0, 0), goal=(4, 0)),
        Robot(id=2, start=(4, 0), goal=(0, 0)),
    ]
    result = cbs_search(grid, robots)
    assert result.success

    conflict = find_first_conflict(result.paths)
    assert conflict is None  # final solution must be truly collision-free


def test_true_1d_corridor_swap_is_unsolvable():
    """
    A single-row, 1-wide corridor with two robots needing to swap ends is
    mathematically unsolvable -- there is no cell to step aside into.
    CBS should correctly report failure rather than hang indefinitely.
    Uses a small node_limit so the test runs fast instead of exhausting
    the full 50,000-node budget.
    """
    grid = Grid([
        [0, 0, 0, 0, 0],
    ])
    robots = [
        Robot(id=1, start=(0, 0), goal=(4, 0)),
        Robot(id=2, start=(4, 0), goal=(0, 0)),
    ]
    result = cbs_search(grid, robots, node_limit=500)
    assert result.success is False


def test_unreachable_goal_fails_gracefully():
    grid = Grid([
        [0, 1, 0],
        [1, 1, 0],
        [0, 1, 0],
    ])
    robots = [Robot(id=1, start=(0, 0), goal=(2, 0))]
    result = cbs_search(grid, robots)
    assert result.success is False


def test_multi_robot_intersection_solves_without_collision():
    grid = Grid([
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ])
    robots = [
        Robot(id=1, start=(0, 2), goal=(4, 2)),
        Robot(id=2, start=(4, 2), goal=(0, 2)),
        Robot(id=3, start=(2, 0), goal=(2, 4)),
        Robot(id=4, start=(2, 4), goal=(2, 0)),
    ]
    result = cbs_search(grid, robots)
    assert result.success

    conflict = find_first_conflict(result.paths)
    assert conflict is None
    assert result.conflicts_detected >= 1  # this layout should force at least one conflict