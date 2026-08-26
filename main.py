"""
main.py
Entry point. For now: load a scenario, run CBS, print results.
PyGame visualization will be wired in during Phase 3.
"""

import sys
from environment.warehouse import load_scenario
from algorithms.cbs import cbs_search


def main(scenario_path: str = "scenarios/simple.json"):
    grid, robots = load_scenario(scenario_path)

    print(f"Loaded scenario: {scenario_path}")
    print(f"Grid size: {grid.width}x{grid.height}")
    print(f"Robots: {len(robots)}")
    print("-" * 40)

    result = cbs_search(grid, robots)

    if not result.success:
        print("FAILED: no collision-free solution found.")
        return

    print(f"SUCCESS: collision-free solution found.")
    print(f"Planning time: {result.planning_time:.4f}s")
    print(f"Nodes expanded: {result.nodes_expanded}")
    print(f"Conflicts detected/resolved: {result.conflicts_detected}")
    print("-" * 40)

    total_cost = 0
    makespan = 0
    for robot in robots:
        path = result.paths[robot.id]
        cost = len(path) - 1
        finish = path[-1][2]
        total_cost += cost
        makespan = max(makespan, finish)
        print(f"Robot {robot.id}: start={robot.start} goal={robot.goal} "
              f"steps={cost} finish_t={finish}")

    print("-" * 40)
    print(f"Total Path Cost: {total_cost}")
    print(f"Makespan: {makespan}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "scenarios/simple.json"
    main(path)