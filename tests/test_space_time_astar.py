"""
tests/test_space_time_astar.py
Tests for the low-level Space-Time A* planner, including constraint handling
and the WAIT action.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from environment.grid import Grid
from algorithms.constraints import ConstraintSet, VertexConstraint, EdgeConstraint
from algorithms.space_time_astar import space_time_astar


def test_single_robot_reaches_goal():
    grid = Grid([
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ])
    constraints = ConstraintSet()
    path = space_time_astar(grid, agent=1, start=(0, 0), goal=(2, 2), constraints=constraints)
    assert path is not None
    assert path[0][:2] == (0, 0)
    assert path[-1][:2] == (2, 2)
    # time must strictly increase by 1 each step
    for i in range(1, len(path)):
        assert path[i][2] == path[i - 1][2] + 1


def test_robot_avoids_obstacles_in_time():
    grid = Grid([
        [0, 1, 0],
        [0, 1, 0],
        [0, 0, 0],
    ])
    constraints = ConstraintSet()
    path = space_time_astar(grid, agent=1, start=(0, 0), goal=(2, 0), constraints=constraints)
    assert path is not None
    for (x, y, t) in path:
        assert grid.data[y][x] == 0


def test_robot_waits_when_vertex_constrained():
    """
    A robot forced off a straight-line cell at a specific time should
    use WAIT (stay in place) rather than fail, if waiting resolves it.
    """
    grid = Grid([
        [0, 0, 0],
    ])
    constraints = ConstraintSet()
    # Block the robot from being at (1,0) at time 1 -> it must wait at (0,0) first
    constraints.add_vertex_constraint(VertexConstraint(agent=1, position=(1, 0), time=1))

    path = space_time_astar(grid, agent=1, start=(0, 0), goal=(2, 0), constraints=constraints)
    assert path is not None
    # The robot must NOT be at (1,0) at time 1
    for (x, y, t) in path:
        assert not (x == 1 and y == 0 and t == 1)
    assert path[-1][:2] == (2, 0)


def test_edge_constraint_prevents_swap():
    grid = Grid([
        [0, 0, 0],
    ])
    constraints = ConstraintSet()
    # Robot 1 is not allowed to move from (0,0) to (1,0) at time 0
    constraints.add_edge_constraint(EdgeConstraint(agent=1, pos_from=(0, 0), pos_to=(1, 0), time=0))

    path = space_time_astar(grid, agent=1, start=(0, 0), goal=(2, 0), constraints=constraints)
    assert path is not None
    # First move (t=0 -> t=1) must NOT be the forbidden edge
    assert not (path[0][:2] == (0, 0) and path[1][:2] == (1, 0) and path[0][2] == 0)


def test_unreachable_goal_returns_none():
    grid = Grid([
        [0, 1, 0],
        [1, 1, 0],
        [0, 1, 0],
    ])
    constraints = ConstraintSet()
    path = space_time_astar(grid, agent=1, start=(0, 0), goal=(2, 0), constraints=constraints, max_time=50)
    assert path is None