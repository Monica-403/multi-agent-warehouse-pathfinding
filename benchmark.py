"""
benchmark.py
Performance evaluation script. Generates random warehouse scenarios at
increasing robot counts, runs CBS on each, and records planning time,
conflicts detected/resolved, total path cost, and makespan.

Each scenario run is capped by both a node limit and a wall-clock time
limit, so a hard instance (e.g. many robots on a tight grid) reports
TIMEOUT and the benchmark moves on, instead of hanging indefinitely.

Usage:
    python benchmark.py
    python benchmark.py --robot-counts 5 10 20 30 --width 20 --height 20
    python benchmark.py --robot-counts 5 10 20 30 --time-limit 30
"""

import argparse
import time
import csv
from typing import List

from environment.grid import Grid
from environment.robot import Robot
from algorithms.cbs import cbs_search
from scenarios.generate_scenario import build_scenario


def run_benchmark(robot_counts: List[int], width: int, height: int,
                   obstacle_density: float, seed: int, node_limit: int,
                   time_limit_seconds: float, output_csv: str):
    results = []

    print(f"{'Robots':>8} | {'Planning Time (s)':>18} | {'Conflicts':>10} | "
          f"{'Total Cost':>10} | {'Makespan':>9} | {'Status':>10}")
    print("-" * 78)

    for count in robot_counts:
        try:
            scenario = build_scenario(width, height, count, obstacle_density, seed)
        except ValueError as e:
            print(f"{count:>8} | Skipped: {e}")
            continue

        grid = Grid(scenario["grid"])
        robots = [
            Robot(id=r["id"], start=tuple(r["start"]), goal=tuple(r["goal"]))
            for r in scenario["robots"]
        ]

        start_time = time.time()
        result = cbs_search(
            grid, robots,
            node_limit=node_limit,
            time_limit_seconds=time_limit_seconds,
        )
        elapsed = time.time() - start_time

        if result.success:
            total_cost = sum(len(p) - 1 for p in result.paths.values())
            makespan = max(p[-1][2] for p in result.paths.values())
            status = "SUCCESS"
        elif result.timed_out:
            total_cost = -1
            makespan = -1
            status = "TIMEOUT"
        else:
            total_cost = -1
            makespan = -1
            status = "FAILED"

        print(f"{count:>8} | {elapsed:>18.4f} | {result.conflicts_detected:>10} | "
              f"{total_cost:>10} | {makespan:>9} | {status:>10}")

        results.append({
            "robots": count,
            "planning_time_sec": round(elapsed, 4),
            "conflicts_detected": result.conflicts_detected,
            "conflicts_resolved": result.conflicts_resolved,
            "nodes_expanded": result.nodes_expanded,
            "total_path_cost": total_cost,
            "makespan": makespan,
            "status": status,
        })

    if output_csv and results:
        with open(output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResults saved to: {output_csv}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Benchmark CBS performance across robot counts.")
    parser.add_argument("--robot-counts", type=int, nargs="+", default=[5, 10, 20, 30])
    parser.add_argument("--width", type=int, default=20)
    parser.add_argument("--height", type=int, default=20)
    parser.add_argument("--obstacle-density", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--node-limit", type=int, default=50000)
    parser.add_argument("--time-limit", type=float, default=30.0,
                         help="Max wall-clock seconds per scenario before giving up")
    parser.add_argument("--output", type=str, default="benchmark_results.csv")
    args = parser.parse_args()

    run_benchmark(
        robot_counts=args.robot_counts,
        width=args.width,
        height=args.height,
        obstacle_density=args.obstacle_density,
        seed=args.seed,
        node_limit=args.node_limit,
        time_limit_seconds=args.time_limit,
        output_csv=args.output,
    )


if __name__ == "__main__":
    main()