"""
tests/test_conflict.py
Tests for vertex and edge conflict detection between robot paths.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from algorithms.conflict import find_first_conflict


def test_no_conflict_when_paths_dont_overlap():
    paths = {
        1: [(0, 0, 0), (1, 0, 1), (2, 0, 2)],
        2: [(0, 5, 0), (1, 5, 1), (2, 5, 2)],
    }
    conflict = find_first_conflict(paths)
    assert conflict is None


def test_vertex_conflict_detected():
    paths = {
        1: [(0, 0, 0), (1, 0, 1), (2, 0, 2)],
        2: [(2, 0, 0), (2, 0, 1), (2, 0, 2)],  # both at (2,0) at t=2
    }
    conflict = find_first_conflict(paths)
    assert conflict is not None
    assert conflict.type == "vertex"
    assert conflict.time == 2
    assert conflict.position_a == (2, 0)
    assert {conflict.agent_a, conflict.agent_b} == {1, 2}


def test_edge_conflict_detected():
    paths = {
        1: [(0, 0, 0), (1, 0, 1)],
        2: [(1, 0, 0), (0, 0, 1)],  # swap positions between t=0 and t=1
    }
    conflict = find_first_conflict(paths)
    assert conflict is not None
    assert conflict.type == "edge"
    assert conflict.time == 0
    assert {conflict.agent_a, conflict.agent_b} == {1, 2}


def test_robot_waiting_at_goal_still_detected_in_conflict():
    """
    Robot 1 finishes early and waits at its goal; robot 2 later moves
    into that same cell -> should be flagged as a vertex conflict.
    """
    paths = {
        1: [(0, 0, 0), (1, 0, 1)],           # finishes at t=1, stays at (1,0) after
        2: [(2, 0, 0), (2, 0, 1), (1, 0, 2)],  # arrives at (1,0) at t=2
    }
    conflict = find_first_conflict(paths)
    assert conflict is not None
    assert conflict.type == "vertex"
    assert conflict.position_a == (1, 0)