# Multi-Agent Warehouse Pathfinding

A warehouse simulator that plans collision-free routes for multiple robots
using Cooperative Conflict-Based Search (CBS). The Flask interface lets you
create and save a warehouse, animate its solution, and request replanning when
temporary obstacles appear.

## Features

- CBS planning with vertex- and edge-conflict resolution.
- A 12 × 12 browser-based warehouse editor for obstacles, robots, and goals.
- Scenario save, edit, and playback.
- Temporary dynamic obstacles with safe replanning from the current simulation
state.
- Light and dark themes.
- A command-line PyGame visualizer and scenario generator.

## Requirements

- Python 3.11 (also used by the CI workflow).
- Packages listed in `requirements.txt`.

## Install and run on Windows

From the repository root in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python web\app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). Choose **Create Custom
Scenario** to place obstacles, robots, and goals. Save the warehouse, then use
**Save & Run CBS** to view the generated paths. The saved scenario can be
reopened from **My Saved Scenario**.

To explicitly enable Flask's interactive debugger during local development:

```powershell
$env:FLASK_DEBUG = "1"
python web\app.py
```

Debug mode is disabled by default. Do not enable it on a publicly reachable or
production server.

## Command-line simulator

The PyGame visualizer can run a JSON scenario directly:

```powershell
python main.py scenarios\simple.json
```

If no scenario path is given, `main.py` uses `scenarios/simple.json`. Close the
visualizer or press **Q** or **Esc** to exit. Playback supports **Space** to
play/pause, **R** to restart, **.** and **,** to step, and **Up/Down** to change
speed.

Generate a scenario with:

```powershell
python scenarios\generate_scenario.py --help
```

## Search limits and failure messages

CBS is an exponential search algorithm in the worst case, so the planner uses
finite limits:

| Context | Limit | What it means |
| --- | ---: | --- |
| Standard CBS search | 50,000 high-level nodes | Maximum CBS conflict-tree nodes expanded |
| Standard CBS search | 30 seconds | Wall-clock search budget |
| Dynamic-obstacle replanning | 10 seconds | Wall-clock budget for the replan |
| Low-level space-time A* | 200 time steps | Maximum planning horizon |

If a robot's goal is unreachable, the saved-scenario page explains that no path
was found. If CBS reaches its node or time limit, the page reports which limit
was reached and suggests reducing the warehouse size or number of robots. A
dynamic-obstacle request returns HTTP 409 with a `failureReason` and a
user-readable message if replanning cannot finish successfully.

The node limit counts high-level CBS nodes, not low-level A* work. Time limits
are checked after each initial low-level route and between CBS node expansions;
a single low-level A* call is not interrupted mid-search.

## Tests

Install the requirements, then run:

```powershell
python -m pytest -q
```

The suite covers A*, CBS, conflict detection, Flask pages, scenario validation
and saving, dynamic-obstacle replanning, and solver-limit reporting.

## Troubleshooting

- **The browser cannot connect:** confirm `python web\app.py` is still running
  and open `http://127.0.0.1:5000`.
- **No saved scenario:** create and save one in the custom editor first.
- **CBS reports a limit:** try fewer robots, fewer obstacles, or a more open
  layout.
- **A dependency is missing:** activate the project virtual environment and
  run `python -m pip install -r requirements.txt`.
