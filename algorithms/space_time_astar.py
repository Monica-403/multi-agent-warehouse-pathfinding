"""
algorithms/space_time_astar.py
Low-level planner: A* over the (x, y, t) state space, respecting vertex and
edge constraints supplied by the CBS high-level search. Includes a WAIT action.
"""

import heapq
from typing import List, Optional, Tuple
from environment.grid import Grid
from algorithms.constraints import ConstraintSet

Position = Tuple[int, int]
PathState = Tuple[int, int, int]  # (x, y, t)


def manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def space_time_astar(
    grid: Grid,
    agent: int,
    start: Position,
    goal: Position,
    constraints: ConstraintSet,
    max_time: int = 200,
) -> Optional[List[PathState]]:
    """
    Returns a path as a list of (x, y, t) tuples, or None if no path exists
    within max_time steps.
    """
    vertex_c, edge_c = constraints.for_agent(agent)

    # Precompute the latest time any constraint applies to this agent, so we know
    # when it's safe to stop worrying about future conflicts once at goal.
    max_constraint_time = 0
    for c in vertex_c:
        max_constraint_time = max(max_constraint_time, c.time)
    for c in edge_c:
        max_constraint_time = max(max_constraint_time, c.time)

    start_state = (start[0], start[1], 0)
    open_set = []
    counter = 0  # tie-breaker for heap
    heapq.heappush(open_set, (manhattan(start, goal), 0, counter, start_state))
    came_from = {}
    g_score = {start_state: 0}
    closed = set()

    while open_set:
        _, cost, _, current = heapq.heappop(open_set)
        cx, cy, ct = current

        if current in closed:
            continue
        closed.add(current)

        # Goal check: must have reached goal AND not have any future constraint
        # forcing it to move away again.
        if (cx, cy) == goal and ct >= max_constraint_time:
            return _reconstruct(came_from, current)

        if ct >= max_time:
            continue

        # Possible moves: 4 directions + WAIT
        moves = grid.neighbors((cx, cy)) + [(cx, cy)]  # last one is WAIT

        for nx, ny in moves:
            nt = ct + 1

            # Vertex constraint check
            if (agent, (nx, ny), nt) in {(v.agent, v.position, v.time) for v in vertex_c}:
                continue
            # Edge constraint check (swap conflict)
            if (agent, (cx, cy), (nx, ny), ct) in {
                (e.agent, e.pos_from, e.pos_to, e.time) for e in edge_c
            }:
                continue

            neighbor = (nx, ny, nt)
            tentative_g = cost + 1

            if tentative_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = tentative_g
                f = tentative_g + manhattan((nx, ny), goal)
                counter += 1
                heapq.heappush(open_set, (f, tentative_g, counter, neighbor))
                came_from[neighbor] = current

    return None  # No path found within max_time


def _reconstruct(came_from, current) -> List[PathState]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path