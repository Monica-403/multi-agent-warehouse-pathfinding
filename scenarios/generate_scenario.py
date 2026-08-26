"""
scenarios/generate_scenario.py
Randomly generates a warehouse scenario (grid + robots) and saves it as JSON.

Usage:
    python scenarios/generate_scenario.py --width 15 --height 15 --robots 20 \
        --obstacle-density 0.15 --seed 42 --output scenarios/dense_warehouse.json
"""

import argparse
import json
import random
from typing import List, Tuple, Set

Position = Tuple[int, int]


def generate_obstacles(width: int, height: int, density: float, rng: random.Random) -> Set[Position]:
    """Places obstacle blocks (2x2 shelf clusters) at random free-ish locations."""
    obstacles = set()
    num_blocks = int((width * height * density) / 4)  # each block covers ~4 cells

    for _ in range(num_blocks):
        bx = rng.randint(0, width - 2)
        by = rng.randint(0, height - 2)
        for dx in range(2):
            for dy in range(2):
                obstacles.add((bx + dx, by + dy))

    return obstacles


def free_cells(width: int, height: int, obstacles: Set[Position]) -> List[Position]:
    return [(x, y) for x in range(width) for y in range(height) if (x, y) not in obstacles]


def generate_robots(num_robots: int, free: List[Position], rng: random.Random) -> List[dict]:
    if num_robots * 2 > len(free):
        raise ValueError(
            f"Not enough free cells ({len(free)}) to place {num_robots} robots "
            f"with unique start+goal positions. Reduce robot count or obstacle density."
        )

    chosen = rng.sample(free, num_robots * 2)
    starts = chosen[:num_robots]
    goals = chosen[num_robots:]

    robots = []
    for i in range(num_robots):
        # Avoid a robot spawning already at its own goal
        if starts[i] == goals[i]:
            goals[i], goals[(i + 1) % num_robots] = goals[(i + 1) % num_robots], goals[i]
        robots.append({"id": i + 1, "start": list(starts[i]), "goal": list(goals[i])})

    return robots


def build_scenario(width: int, height: int, num_robots: int, obstacle_density: float, seed: int) -> dict:
    rng = random.Random(seed)
    obstacles = generate_obstacles(width, height, obstacle_density, rng)
    free = free_cells(width, height, obstacles)
    robots = generate_robots(num_robots, free, rng)

    grid = [[1 if (x, y) in obstacles else 0 for x in range(width)] for y in range(height)]
    return {"grid": grid, "robots": robots}


def main():
    parser = argparse.ArgumentParser(description="Generate a random warehouse scenario.")
    parser.add_argument("--width", type=int, default=15, help="Grid width")
    parser.add_argument("--height", type=int, default=15, help="Grid height")
    parser.add_argument("--robots", type=int, default=10, help="Number of robots")
    parser.add_argument("--obstacle-density", type=float, default=0.1,
                         help="Fraction of grid area covered by obstacles (0.0 - 0.5)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (for reproducibility)")
    parser.add_argument("--output", type=str, default="scenarios/generated.json", help="Output file path")
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    scenario = build_scenario(args.width, args.height, args.robots, args.obstacle_density, seed)

    with open(args.output, "w") as f:
        json.dump(scenario, f, indent=2)

    print(f"Generated scenario: {args.output}")
    print(f"  Grid: {args.width}x{args.height}")
    print(f"  Robots: {args.robots}")
    print(f"  Obstacle density: {args.obstacle_density}")
    print(f"  Seed: {seed}  (reuse this seed to reproduce the exact same scenario)")


if __name__ == "__main__":
    main()