from flask import Flask, render_template, request, jsonify
import sys
from pathlib import Path
import json

# =========================================================
# PROJECT PATH
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from environment.warehouse import load_scenario
from algorithms.cbs import cbs_search


app = Flask(__name__)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# COMMON SCENARIO RUNNER
# =========================================================

def run_scenario(scenario_file):

    scenario_path = (
        PROJECT_ROOT
        / "scenarios"
        / scenario_file
    )


    grid, robots = load_scenario(
        str(scenario_path)
    )


    # Run CBS

    result = cbs_search(
        grid,
        robots
    )


    robot_results = []

    animation_paths = {}


    if result.success:

        for robot in robots:

            path = result.paths[
                robot.id
            ]


            robot_results.append({

                "id": robot.id,

                "start": robot.start,

                "goal": robot.goal,

                "steps":
                    len(path) - 1,

                "finish_time":
                    path[-1][2]

            })


            # Convert CBS path into
            # JavaScript-friendly format

            animation_paths[
                str(robot.id)
            ] = [

                [
                    state[0],
                    state[1]
                ]

                for state in path

            ]


    # =====================================================
    # WAREHOUSE CELLS
    # =====================================================

    cells = {}


    # Obstacles

    for y in range(
        grid.height
    ):

        for x in range(
            grid.width
        ):

            if grid.data[y][x] == 1:

                cells[
                    f"{x},{y}"
                ] = {

                    "type":
                        "obstacle"

                }


    # Robots and goals

    for robot in robots:

        start_key = (
            f"{robot.start[0]},"
            f"{robot.start[1]}"
        )


        cells[start_key] = {

            "type":
                "robot",

            "id":
                robot.id

        }


        goal_key = (
            f"{robot.goal[0]},"
            f"{robot.goal[1]}"
        )


        cells[goal_key] = {

            "type":
                "goal",

            "id":
                robot.id

        }


    return {

        "success":
            result.success,

        "grid":
            grid,

        "robots":
            robot_results,

        "cells":
            cells,

        "animation_paths":
            animation_paths,

        "total_cost":
            sum(
                robot["steps"]
                for robot in robot_results
            ),

        "makespan":
            max(
                (
                    robot["finish_time"]
                    for robot in robot_results
                ),
                default=0
            ),

        "planning_time":
            result.planning_time,

        "conflicts":
            result.conflicts_detected,

        "nodes":
            result.nodes_expanded

    }


# =========================================================
# PREDEFINED SCENARIO
# =========================================================

@app.route("/predefined")
def predefined():

    data = run_scenario(
        "simple.json"
    )


    return render_template(
        "predefined.html",
        **data
    )


# =========================================================
# SAVED SCENARIO
# =========================================================

@app.route("/saved")
def saved():

    dynamic_file = (
        PROJECT_ROOT
        / "scenarios"
        / "dynamic.json"
    )


    if not dynamic_file.exists():

        return render_template(

            "saved.html",

            scenario_exists=False

        )


    data = run_scenario(
        "dynamic.json"
    )


    data[
        "scenario_exists"
    ] = True


    return render_template(
        "saved.html",
        **data
    )


# =========================================================
# CREATE NEW CUSTOM SCENARIO
# =========================================================

@app.route("/custom")
def custom():

    return render_template(

        "custom.html",

        edit_mode=False,

        saved_scenario=None

    )


# =========================================================
# MODIFY EXISTING CUSTOM SCENARIO
# =========================================================

@app.route("/custom/edit")
def edit_custom():

    dynamic_file = (
        PROJECT_ROOT
        / "scenarios"
        / "dynamic.json"
    )


    # No saved scenario

    if not dynamic_file.exists():

        return render_template(

            "custom.html",

            edit_mode=False,

            saved_scenario=None

        )


    try:

        with open(
            dynamic_file,
            "r",
            encoding="utf-8"
        ) as file:

            saved_scenario = json.load(
                file
            )


    except Exception:

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

@app.route(
    "/custom/save",
    methods=["POST"]
)
def save_custom():

    data = request.get_json()


    if not data:

        return jsonify({

            "success":
                False,

            "message":
                "No scenario data received."

        }), 400


    grid = data.get(
        "grid"
    )


    robots = data.get(
        "robots",
        []
    )


    # =====================================================
    # GRID VALIDATION
    # =====================================================

    if not grid:

        return jsonify({

            "success":
                False,

            "message":
                "Grid cannot be empty."

        }), 400


    height = len(
        grid
    )


    width = len(
        grid[0]
    )


    if (
        height != 12
        or width != 12
    ):

        return jsonify({

            "success":
                False,

            "message":
                "Grid must be 12 x 12."

        }), 400


    # =====================================================
    # ROBOT VALIDATION
    # =====================================================

    robot_data = []


    for robot in robots:

        robot_id = robot.get(
            "id"
        )

        start = robot.get(
            "start"
        )

        goal = robot.get(
            "goal"
        )


        if start is None:

            return jsonify({

                "success":
                    False,

                "message":
                    f"Robot {robot_id} has no start position."

            }), 400


        if goal is None:

            return jsonify({

                "success":
                    False,

                "message":
                    f"Robot {robot_id} has no goal."

            }), 400


        robot_data.append({

            "id":
                robot_id,

            "start":
                start,

            "goal":
                goal

        })


    # =====================================================
    # SAVE TO THE ONE dynamic.json FILE
    # =====================================================

    scenario_path = (
        PROJECT_ROOT
        / "scenarios"
        / "dynamic.json"
    )


    scenario = {

        "grid":
            grid,

        "robots":
            robot_data

    }


    try:

        with open(
            scenario_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(

                scenario,

                file,

                indent=2

            )


    except Exception as error:

        return jsonify({

            "success":
                False,

            "message":
                f"Could not save scenario: {error}"

        }), 500


    return jsonify({

        "success":
            True,

        "message":
            "Scenario saved successfully to dynamic.json."

    })


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )