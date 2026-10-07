"""
main.py
Entry point.

Loads a warehouse scenario, runs CBS, prints metrics,
and launches the PyGame visualization.
"""

import sys

from environment.warehouse import load_scenario
from algorithms.cbs import cbs_search
from simulation.animation import run_simulation


def main(
    scenario_path: str = "scenarios/simple.json",
    visualize: bool = True
):

    # =========================================================
    # 1. LOAD SCENARIO
    # =========================================================

    grid, robots = load_scenario(scenario_path)

    print(f"Loaded scenario: {scenario_path}")
    print(f"Grid size: {grid.width}x{grid.height}")
    print(f"Robots: {len(robots)}")
    print("-" * 40)

    # =========================================================
    # 2. RUN CBS
    # =========================================================

    print("Running CBS...")

    result = cbs_search(
        grid,
        robots
    )

    # =========================================================
    # 3. CHECK RESULT
    # =========================================================

    if not result.success:

        print("FAILED: no collision-free solution found.")

        print(
            f"Conflicts encountered: "
            f"{result.conflicts_detected}"
        )

        print(
            f"Nodes expanded: "
            f"{result.nodes_expanded}"
        )

        print(
            f"Search time: "
            f"{result.planning_time:.4f}s"
        )

        if result.timed_out:
            print("Reason: CBS search timed out.")

        if visualize:

            print(
                "Opening visualizer to show failure state..."
            )

            run_simulation(
                grid,
                robots,
                result
            )

        return

    # =========================================================
    # 4. CALCULATE METRICS
    # =========================================================

    total_cost = 0
    makespan = 0

    for robot in robots:

        path = result.paths[robot.id]

        cost = len(path) - 1

        finish = path[-1][2]

        total_cost += cost

        makespan = max(
            makespan,
            finish
        )

        print(
            f"Robot {robot.id}: "
            f"start={robot.start} "
            f"goal={robot.goal} "
            f"steps={cost} "
            f"finish_t={finish}"
        )

    # =========================================================
    # 5. PRINT RESULTS
    # =========================================================

    print("-" * 40)

    print(
        f"Total Path Cost: {total_cost}"
    )

    print(
        f"Makespan: {makespan}"
    )

    print(
        f"Planning Time: "
        f"{result.planning_time:.4f}s"
    )

    print(
        f"Conflicts Detected: "
        f"{result.conflicts_detected}"
    )

    print(
        f"Nodes Expanded: "
        f"{result.nodes_expanded}"
    )

    # =========================================================
    # 6. LAUNCH VISUALIZER
    # =========================================================

    if visualize:

        print("-" * 40)

        print(
            "Launching PyGame visualizer..."
            " (close window or press Q/ESC to quit)"
        )

        run_simulation(
            grid,
            robots,
            result
        )


# =============================================================
# PROGRAM START
# =============================================================

if __name__ == "__main__":

    # ---------------------------------------------------------
    # Default = predefined scenario
    #
    # To run a custom scenario:
    #
    # python main.py scenarios/dynamic.json
    # ---------------------------------------------------------

    path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "scenarios/simple.json"
    )

    main(path)