"""
algorithms/cbs.py
High-level Conflict-Based Search: builds a search tree over constraint sets,
resolving vertex/edge conflicts by branching and replanning affected robots.
"""

import heapq
import itertools
import time as time_module
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from environment.grid import Grid
from environment.robot import Robot
from algorithms.constraints import ConstraintSet, VertexConstraint, EdgeConstraint
from algorithms.space_time_astar import space_time_astar
from algorithms.conflict import find_first_conflict

PathState = Tuple[int, int, int]


@dataclass
class CBSNode:
    constraints: ConstraintSet
    paths: Dict[int, List[PathState]]
    cost: int = 0

    def compute_cost(self):
        self.cost = sum(len(p) - 1 for p in self.paths.values())
        return self.cost


@dataclass
class CBSResult:
    success: bool
    paths: Dict[int, List[PathState]]
    planning_time: float
    conflicts_detected: int
    conflicts_resolved: int
    nodes_expanded: int


def cbs_search(
    grid: Grid,
    robots: List[Robot],
    max_time: int = 200,
    node_limit: int = 50000,
) -> CBSResult:
    start_time = time_module.time()
    conflicts_detected = 0
    nodes_expanded = 0

    # --- Root node: plan every robot independently, ignoring other robots ---
    root_constraints = ConstraintSet()
    root_paths = {}
    for robot in robots:
        path = space_time_astar(grid, robot.id, robot.start, robot.goal, root_constraints, max_time)
        if path is None:
            return CBSResult(False, {}, time_module.time() - start_time, 0, 0, 0)
        root_paths[robot.id] = path

    root = CBSNode(constraints=root_constraints, paths=root_paths)
    root.compute_cost()

    counter = itertools.count()
    open_list = []
    heapq.heappush(open_list, (root.cost, next(counter), root))

    while open_list:
        nodes_expanded += 1
        if nodes_expanded > node_limit:
            return CBSResult(False, {}, time_module.time() - start_time,
                              conflicts_detected, conflicts_detected, nodes_expanded)

        _, _, node = heapq.heappop(open_list)

        conflict = find_first_conflict(node.paths)

        if conflict is None:
            # No conflicts left -> valid, collision-free solution
            return CBSResult(
                True, node.paths, time_module.time() - start_time,
                conflicts_detected, conflicts_detected, nodes_expanded,
            )

        conflicts_detected += 1

        # Branch into two children: constrain agent_a, and constrain agent_b
        for agent in (conflict.agent_a, conflict.agent_b):
            child_constraints = node.constraints.copy()

            if conflict.type == "vertex":
                pos = conflict.position_a  # same as position_b for vertex conflicts
                child_constraints.add_vertex_constraint(
                    VertexConstraint(agent, pos, conflict.time)
                )
            else:  # edge conflict
                if agent == conflict.agent_a:
                    pos_from, pos_to = conflict.position_a, conflict.position_b
                else:
                    pos_from, pos_to = conflict.position_b, conflict.position_a
                child_constraints.add_edge_constraint(
                    EdgeConstraint(agent, pos_from, pos_to, conflict.time)
                )

            # Replan only the affected robot
            robot_obj = next(r for r in robots if r.id == agent)
            new_path = space_time_astar(
                grid, agent, robot_obj.start, robot_obj.goal, child_constraints, max_time
            )

            if new_path is None:
                continue  # this branch is infeasible, discard

            child_paths = dict(node.paths)
            child_paths[agent] = new_path

            child_node = CBSNode(constraints=child_constraints, paths=child_paths)
            child_node.compute_cost()
            heapq.heappush(open_list, (child_node.cost, next(counter), child_node))

    return CBSResult(False, {}, time_module.time() - start_time,
                      conflicts_detected, conflicts_detected, nodes_expanded)