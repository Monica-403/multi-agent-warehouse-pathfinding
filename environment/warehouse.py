"""
environment/warehouse.py
Loads a warehouse scenario (grid + robots) from a JSON file.
"""

import json
from typing import List, Tuple
from environment.grid import Grid
from environment.robot import Robot


def load_scenario(path: str) -> Tuple[Grid, List[Robot]]:
    with open(path, "r") as f:
        data = json.load(f)

    grid = Grid(data["grid"])
    robots = []
    for r in data["robots"]:
        robots.append(Robot(id=r["id"], start=tuple(r["start"]), goal=tuple(r["goal"])))

    return grid, robots


def save_scenario(path: str, grid: Grid, robots: List[Robot]):
    data = {
        "grid": grid.data,
        "robots": [{"id": r.id, "start": list(r.start), "goal": list(r.goal)} for r in robots],
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)