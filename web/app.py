import sys
import json
from pathlib import Path

from flask import Flask, render_template, request, jsonify

# =========================================================
# PROJECT PATH
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from environment.robot import Robot
from environment.warehouse import load_scenario
from algorithms.cbs import cbs_search
from agents.dynamic_obstacle_agent import DynamicObstacleAgent

app = Flask(__name__)
dynamic_obstacle_agent = DynamicObstacleAgent()


# =========================================================
# COMMON SCENARIO RUNNER
# =========================================================

def run_scenario(scenario_file):
    scenario_path = PROJECT_ROOT / "scenarios" / scenario_file
    grid, robots = load_scenario(str(scenario_path))
    result = cbs_search(grid, robots)

    robot_results = []
    animation_paths = {}

    if result.success:
        for robot in robots:
            path = result.paths[robot.id]

            robot_results.append({
                "id": robot.id,
                "start": robot.start,
                "goal": robot.goal,
                "steps": len(path) - 1,
                "finish_time": path[-1][2]
            })

            animation_paths[str(robot.id)] = [
                [state[0], state[1]] for state in path
            ]

    cells = {}

    for y in range(grid.height):
        for x in range(grid.width):
            if grid.data[y][x] == 1:
                cells[f"{x},{y}"] = {"type": "obstacle"}

    for robot in robots:
        cells[f"{robot.start[0]},{robot.start[1]}"] = {
            "type": "robot",
            "id": robot.id
        }

        cells[f"{robot.goal[0]},{robot.goal[1]}"] = {
            "type": "goal",
            "id": robot.id
        }

    return {
        "success": result.success,
        "grid": grid,
        "robots": robot_results,
        "cells": cells,
        "animation_paths": animation_paths,
        "total_cost": sum(r["steps"] for r in robot_results),
        "makespan": max(
            (r["finish_time"] for r in robot_results),
            default=0
        ),
        "planning_time": result.planning_time,
        "conflicts": result.conflicts_detected,
        "nodes": result.nodes_expanded
    }


# =========================================================
# HOME AND SCENARIO PAGES
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predefined")
def predefined():
    return render_template(
        "predefined.html",
        **run_scenario("simple.json")
    )


@app.route("/saved")
def saved():
    dynamic_file = PROJECT_ROOT / "scenarios" / "dynamic.json"

    if not dynamic_file.exists():
        return render_template(
            "saved.html",
            scenario_exists=False
        )

    data = run_scenario("dynamic.json")
    data["scenario_exists"] = True

    return render_template("saved.html", **data)


@app.route("/custom")
def custom():
    return render_template(
        "custom.html",
        edit_mode=False,
        saved_scenario=None
    )


@app.route("/custom/edit")
def edit_custom():
    dynamic_file = PROJECT_ROOT / "scenarios" / "dynamic.json"

    if not dynamic_file.exists():
        return render_template(
            "custom.html",
            edit_mode=False,
            saved_scenario=None
        )

    try:
        with open(dynamic_file, "r", encoding="utf-8") as file:
            saved_scenario = json.load(file)

    except Exception:
        app.logger.exception("Could not load saved scenario")

        return render_template(
            "custom.html",
            edit_mode=False,
            saved_scenario=None
        )

    return render_template(
        "custom.html",
        edit_mode=True,
        saved_scenario=saved_scenario
    )


# =========================================================
# SAVE CUSTOM SCENARIO
# =========================================================

@app.route("/custom/save", methods=["POST"])
def save_custom():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "No scenario data received."
        }), 400

    grid_data = data.get("grid")
    robots = data.get("robots", [])

    if (
        not isinstance(grid_data, list)
        or len(grid_data) != 12
        or any(
            not isinstance(row, list) or len(row) != 12
            for row in grid_data
        )
    ):
        return jsonify({
            "success": False,
            "message": "Grid must be 12 x 12 with equal row lengths."
        }), 400

    if not isinstance(robots, list):
        return jsonify({
            "success": False,
            "message": "Robots must be a list."
        }), 400

    robot_data = []
    robot_ids = set()
    occupied_starts = set()

    for robot in robots:
        if not isinstance(robot, dict):
            return jsonify({
                "success": False,
                "message": "Invalid robot data."
            }), 400

        robot_id = robot.get("id")
        start = robot.get("start")
        goal = robot.get("goal")

        if (
            robot_id is None
            or start is None
            or goal is None
            or not isinstance(start, list)
            or not isinstance(goal, list)
            or len(start) != 2
            or len(goal) != 2
            or any(type(v) is not int for v in start + goal)
        ):
            return jsonify({
                "success": False,
                "message": (
                    f"Invalid start, goal, or ID for robot {robot_id}."
                )
            }), 400

        sx, sy = start
        gx, gy = goal

        if not all(0 <= v < 12 for v in (sx, sy, gx, gy)):
            return jsonify({
                "success": False,
                "message": f"Robot {robot_id} is outside the grid."
            }), 400

        if (
            grid_data[sy][sx] == 1
            or grid_data[gy][gx] == 1
        ):
            return jsonify({
                "success": False,
                "message": f"Robot {robot_id} start or goal is blocked."
            }), 400

        if str(robot_id) in robot_ids:
            return jsonify({
                "success": False,
                "message": "Robot IDs must be unique."
            }), 400

        if tuple(start) in occupied_starts:
            return jsonify({
                "success": False,
                "message": "Two robots cannot share a start position."
            }), 400

        robot_ids.add(str(robot_id))
        occupied_starts.add(tuple(start))

        robot_data.append({
            "id": robot_id,
            "start": start,
            "goal": goal
        })

    scenario_path = PROJECT_ROOT / "scenarios" / "dynamic.json"

    try:
        with open(scenario_path, "w", encoding="utf-8") as file:
            json.dump(
                {
                    "grid": grid_data,
                    "robots": robot_data
                },
                file,
                indent=2
            )

    except Exception:
        app.logger.exception("Could not save custom scenario")

        return jsonify({
            "success": False,
            "message": "Could not save the scenario."
        }), 500

    return jsonify({
        "success": True,
        "message": "Scenario saved successfully to dynamic.json."
    })


# =========================================================
# PATH SAFETY VALIDATION
# =========================================================

def validate_robot_conflicts(paths):
    """
    Detect vertex conflicts and edge swaps.

    A robot remains at its final position after its path ends.
    """

    if not paths:
        return False, "No robot paths were returned."

    if any(not path for path in paths.values()):
        return False, "An empty robot path was returned."

    max_length = max(len(path) for path in paths.values())

    for t in range(max_length):
        positions = [
            path[min(t, len(path) - 1)]
            for path in paths.values()
        ]

        if len(positions) != len(set(positions)):
            return False, f"Vertex conflict at time {t}."

        if t > 0:
            previous = [
                path[min(t - 1, len(path) - 1)]
                for path in paths.values()
            ]

            for i in range(len(positions)):
                for j in range(i + 1, len(positions)):
                    if (
                        previous[i] == positions[j]
                        and previous[j] == positions[i]
                        and previous[i] != positions[j]
                    ):
                        return False, (
                            f"Edge-swap conflict at time {t}."
                        )

    return True, "No robot-to-robot conflicts found."


# =========================================================
# DYNAMIC OBSTACLE RESPONSE — MULTI-OBSTACLE CBS
# =========================================================

@app.route("/dynamic-obstacle", methods=["POST"])
def dynamic_obstacle():
    data = request.get_json(silent=True) or {}

    # -----------------------------------------------------
    # 1. Read and validate request
    # -----------------------------------------------------

    try:
        x = data["x"]
        y = data["y"]
        current_time = data["currentTime"]
        animation_paths = data["animationPaths"]
        active_obstacles = data.get("activeObstacles", [])

        if any(
            type(v) is not int
            for v in (x, y, current_time)
        ):
            raise ValueError("Coordinates and time must be integers.")

        if current_time < 0 or not isinstance(animation_paths, dict):
            raise ValueError("Invalid time or animation paths.")

        if not isinstance(active_obstacles, list):
            raise ValueError("Invalid active obstacles.")

    except (KeyError, TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid obstacle request data."
        }), 400

    scenario_path = PROJECT_ROOT / "scenarios" / "dynamic.json"

    if not scenario_path.exists():
        return jsonify({
            "success": False,
            "message": "No saved scenario exists."
        }), 404

    try:
        original_grid, original_robots = load_scenario(
            str(scenario_path)
        )

        # -------------------------------------------------
        # 2. Create an independent temporary grid
        # -------------------------------------------------

        grid = type(original_grid)(
            [row[:] for row in original_grid.data]
        )

        if (
            not grid.in_bounds((x, y))
            or not grid.is_free((x, y))
        ):
            return jsonify({
                "success": False,
                "message": (
                    "Selected cell is outside the grid or blocked."
                )
            }), 400

        # -------------------------------------------------
        # 3. Collect ALL active temporary obstacles
        # -------------------------------------------------

        obstacle_set = {(x, y)}

        for obstacle in active_obstacles:
            if not isinstance(obstacle, dict):
                return jsonify({
                    "success": False,
                    "message": "Invalid obstacle entry."
                }), 400

            ox = obstacle.get("x")
            oy = obstacle.get("y")

            if type(ox) is not int or type(oy) is not int:
                return jsonify({
                    "success": False,
                    "message": (
                        "Obstacle coordinates must be integers."
                    )
                }), 400

            if not grid.in_bounds((ox, oy)):
                return jsonify({
                    "success": False,
                    "message": (
                        f"Obstacle {(ox, oy)} is outside the grid."
                    )
                }), 400

            obstacle_set.add((ox, oy))

        # Never block a robot goal.
        for ox, oy in obstacle_set:
            if any(
                robot.goal == (ox, oy)
                for robot in original_robots
            ):
                return jsonify({
                    "success": False,
                    "message": f"Obstacle {(ox, oy)} overlaps a goal."
                }), 409

        # -------------------------------------------------
        # 4. Validate old paths and determine current positions
        # -------------------------------------------------

        validated_paths = {}
        current_positions = {}

        for robot in original_robots:
            key = str(robot.id)
            path = animation_paths.get(key)

            if not isinstance(path, list) or not path:
                return jsonify({
                    "success": False,
                    "message": f"Missing path for robot {robot.id}."
                }), 400

            checked_path = []

            for position in path:
                if (
                    not isinstance(position, list)
                    or len(position) != 2
                    or any(type(v) is not int for v in position)
                ):
                    return jsonify({
                        "success": False,
                        "message": f"Invalid path for robot {robot.id}."
                    }), 400

                pos = tuple(position)

                if (
                    not grid.in_bounds(pos)
                    or not grid.is_free(pos)
                ):
                    return jsonify({
                        "success": False,
                        "message": (
                            f"Existing path for robot {robot.id} "
                            "contains an invalid cell."
                        )
                    }), 409

                checked_path.append(pos)

            validated_paths[key] = checked_path
            current_positions[robot.id] = checked_path[
                min(current_time, len(checked_path) - 1)
            ]

        # Reject any obstacle beneath a robot.
        if any(
            obstacle in current_positions.values()
            for obstacle in obstacle_set
        ):
            return jsonify({
                "success": False,
                "message": (
                    "An obstacle overlaps a current robot position."
                )
            }), 409

        # -------------------------------------------------
        # 5. Validate historical paths
        # -------------------------------------------------

        history = {
            key: path[:current_time + 1]
            for key, path in validated_paths.items()
        }

        history_ok, history_message = validate_robot_conflicts(
            history
        )

        if not history_ok:
            return jsonify({
                "success": False,
                "message": (
                    f"Existing animation is unsafe: {history_message}"
                )
            }), 409

        # -------------------------------------------------
        # 6. Block every active obstacle on the temporary grid
        # -------------------------------------------------

        for ox, oy in obstacle_set:
            grid.data[oy][ox] = 1

        # -------------------------------------------------
        # 7. Build robots at their current positions
        # -------------------------------------------------

        replanning_robots = []

        for robot in original_robots:
            start = current_positions[robot.id]

            if not grid.is_valid(start):
                return jsonify({
                    "success": False,
                    "message": (
                        f"Robot {robot.id} cannot start safely."
                    )
                }), 409

            replanning_robots.append(
                Robot(
                    id=robot.id,
                    start=start,
                    goal=robot.goal
                )
            )

        # -------------------------------------------------
        # 8. Run CBS on the grid with all obstacles
        # -------------------------------------------------

        result = cbs_search(
            grid,
            replanning_robots,
            max_time=200,
            time_limit_seconds=10.0
        )

        if not result.success:
            return jsonify({
                "success": False,
                "message": (
                    "CBS could not find a safe plan around all "
                    "active obstacles."
                )
            }), 409

        # -------------------------------------------------
        # 9. Combine historical prefixes with new paths
        # -------------------------------------------------

        combined_paths = {}

        for robot in original_robots:
            key = str(robot.id)
            old_path = validated_paths[key]
            new_path = result.paths[robot.id]

            prefix = old_path[:current_time + 1]
            suffix = [
                (state[0], state[1])
                for state in new_path[1:]
            ]

            combined_paths[key] = prefix + suffix

        paths_from_pause = {
            key: path[current_time:]
            for key, path in combined_paths.items()
        }

        # -------------------------------------------------
        # 10. Reject paths entering ANY active obstacle
        # -------------------------------------------------

        for robot_id, path in paths_from_pause.items():
            for pos in path:
                if pos in obstacle_set:
                    return jsonify({
                        "success": False,
                        "message": (
                            f"Unsafe plan rejected: robot {robot_id} "
                            f"enters obstacle {pos}."
                        )
                    }), 409

        # Keep agent status tracking.
        if not dynamic_obstacle_agent.validate_paths(
            paths_from_pause, (x, y)
        ):
            return jsonify({
                "success": False,
                "message": (
                    "Dynamic Obstacle Agent rejected the plan: "
                    f"{dynamic_obstacle_agent.last_status}."
                )
            }), 409

        # -------------------------------------------------
        # 11. Check robot collisions and edge swaps
        # -------------------------------------------------

        paths_ok, paths_message = validate_robot_conflicts(
            combined_paths
        )

        if not paths_ok:
            return jsonify({
                "success": False,
                "message": (
                    f"Replanned paths rejected: {paths_message}"
                )
            }), 409

        # -------------------------------------------------
        # 12. Check all future positions against the grid
        # -------------------------------------------------

        for robot_id, path in combined_paths.items():
            for t in range(current_time, len(path)):
                pos = path[t]

                if (
                    not grid.in_bounds(pos)
                    or not grid.is_free(pos)
                ):
                    return jsonify({
                        "success": False,
                        "message": (
                            f"Unsafe path rejected for robot {robot_id} "
                            f"at time {t}, position {pos}."
                        )
                    }), 409

        # -------------------------------------------------
        # 13. Debug output
        # -------------------------------------------------

        print("\n========== DYNAMIC OBSTACLE DEBUG ==========")
        print("ACTIVE OBSTACLES:", sorted(obstacle_set))
        print("CURRENT TIME:", current_time)

        for robot_id, path in combined_paths.items():
            enters_obstacle = any(
                pos in obstacle_set
                for pos in path[current_time:]
            )

            print(
                f"Robot {robot_id} enters an obstacle:",
                enters_obstacle
            )

        print("============================================\n")

        # -------------------------------------------------
        # 14. Return updated paths
        # -------------------------------------------------

        js_paths = {
            key: [list(pos) for pos in path]
            for key, path in combined_paths.items()
        }

        return jsonify({
            "success": True,
            "message": (
                f"Replanning succeeded around {len(obstacle_set)} "
                "active temporary obstacle(s)."
            ),
            "obstacle": {
                "x": x,
                "y": y
            },
            "activeObstacles": [
                {"x": ox, "y": oy}
                for ox, oy in sorted(obstacle_set)
            ],
            "animationPaths": js_paths,
            "maxTime": max(
                (
                    len(path) - 1
                    for path in combined_paths.values()
                ),
                default=current_time
            ),
            "planningTime": result.planning_time,
            "conflicts": result.conflicts_detected,
            "nodes": result.nodes_expanded
        })

    except Exception:
        app.logger.exception("Dynamic obstacle replanning failed")

        return jsonify({
            "success": False,
            "message": (
                "An internal error occurred during replanning."
            )
        }), 500


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)