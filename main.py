"""
main.py
Entry point. Loads a scenario, runs CBS, prints metrics, and launches the
PyGame visualization of the collision-free paths.
"""

import sys
from environment.warehouse import load_scenario
from algorithms.cbs import cbs_search
from simulation.animation import run_simulation


def main(scenario_path: str = "scenarios/simple.json", visualize: bool = True):
    grid, robots = load_scenario(scenario_path)

    print(f"Loaded scenario: {scenario_path}")
    print(f"Grid size: {grid.width}x{grid.height}")
    print(f"Robots: {len(robots)}")
    print("-" * 40)

    result = cbs_search(grid, robots)

    if not result.success:
        print("FAILED: no collision-free solution found.")
        print(f"Conflicts encountered: {result.conflicts_detected}")
        print(f"Nodes expanded: {result.nodes_expanded}")
        print(f"Search time: {result.planning_time:.4f}s")
        if visualize:
            print("Opening visualizer to show failure state...")
            run_simulation(grid, robots, result)
        return

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

    if visualize:
        print("-" * 40)
        print("Launching PyGame visualizer... (close window or press Q/ESC to quit)")
        run_simulation(grid, robots, result)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "scenarios/simple.json"
    main(path)