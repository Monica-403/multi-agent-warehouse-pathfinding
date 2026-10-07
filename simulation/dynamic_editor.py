import pygame
import sys
import json
import os
import subprocess


# ============================================================
# CONFIGURATION
# ============================================================

ROWS = 12
COLS = 12
CELL_SIZE = 55

GRID_WIDTH = COLS * CELL_SIZE
GRID_HEIGHT = ROWS * CELL_SIZE

BOTTOM_PANEL_HEIGHT = 155

WIDTH = GRID_WIDTH
HEIGHT = GRID_HEIGHT + BOTTOM_PANEL_HEIGHT


# ============================================================
# COLORS
# ============================================================

WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
GRAY = (180, 180, 180)
DARK_GRAY = (70, 70, 70)

OBSTACLE_COLOR = (80, 80, 80)
GOAL_COLOR = (40, 180, 80)

PANEL_COLOR = (220, 220, 220)

BUTTON_COLOR = (200, 200, 200)
BUTTON_ACTIVE_COLOR = (100, 160, 230)
RUN_BUTTON_COLOR = (80, 180, 100)

TEXT_COLOR = (20, 20, 20)

ROBOT_COLORS = [
    (220, 70, 70),
    (70, 100, 220),
    (240, 160, 50),
    (170, 70, 190),
    (40, 160, 160),
    (220, 100, 150),
    (100, 150, 60),
    (120, 80, 200),
]


# ============================================================
# DRAW GRID
# ============================================================

def draw_grid(screen, obstacles, robots, goals, current_mode):

    screen.fill(WHITE)

    # --------------------------------------------------------
    # Draw cells
    # --------------------------------------------------------

    for row in range(ROWS):

        for col in range(COLS):

            x = col * CELL_SIZE
            y = row * CELL_SIZE

            rect = pygame.Rect(
                x,
                y,
                CELL_SIZE,
                CELL_SIZE
            )

            # Obstacle
            if (row, col) in obstacles:

                pygame.draw.rect(
                    screen,
                    OBSTACLE_COLOR,
                    rect
                )

            # Free cell
            else:

                pygame.draw.rect(
                    screen,
                    WHITE,
                    rect
                )

            # Cell border
            pygame.draw.rect(
                screen,
                GRAY,
                rect,
                1
            )

    # --------------------------------------------------------
    # Draw goals
    # --------------------------------------------------------

    font_goal = pygame.font.SysFont(
        "arial",
        16,
        bold=True
    )

    for robot_id, goal in goals.items():

        row, col = goal

        x = col * CELL_SIZE
        y = row * CELL_SIZE

        goal_rect = pygame.Rect(
            x + 8,
            y + 8,
            CELL_SIZE - 16,
            CELL_SIZE - 16
        )

        pygame.draw.rect(
            screen,
            GOAL_COLOR,
            goal_rect,
            3
        )

        text = font_goal.render(
            f"G{robot_id}",
            True,
            GOAL_COLOR
        )

        text_rect = text.get_rect(
            center=goal_rect.center
        )

        screen.blit(
            text,
            text_rect
        )

    # --------------------------------------------------------
    # Draw robots
    # --------------------------------------------------------

    font_robot = pygame.font.SysFont(
        "arial",
        17,
        bold=True
    )

    for robot_id, position in robots.items():

        row, col = position

        center_x = (
            col * CELL_SIZE
            + CELL_SIZE // 2
        )

        center_y = (
            row * CELL_SIZE
            + CELL_SIZE // 2
        )

        color = ROBOT_COLORS[
            (robot_id - 1) % len(ROBOT_COLORS)
        ]

        # Robot circle
        pygame.draw.circle(
            screen,
            color,
            (center_x, center_y),
            18
        )

        # Robot border
        pygame.draw.circle(
            screen,
            BLACK,
            (center_x, center_y),
            18,
            2
        )

        # Robot ID
        text = font_robot.render(
            str(robot_id),
            True,
            WHITE
        )

        text_rect = text.get_rect(
            center=(center_x, center_y)
        )

        screen.blit(
            text,
            text_rect
        )

    # ========================================================
    # BOTTOM PANEL
    # ========================================================

    panel_y = GRID_HEIGHT

    pygame.draw.rect(
        screen,
        PANEL_COLOR,
        (
            0,
            panel_y,
            WIDTH,
            BOTTOM_PANEL_HEIGHT
        )
    )

    pygame.draw.line(
        screen,
        DARK_GRAY,
        (0, panel_y),
        (WIDTH, panel_y),
        2
    )

    # --------------------------------------------------------
    # Buttons
    # --------------------------------------------------------

    buttons = [
        ("1 OBSTACLE", "obstacle"),
        ("2 ROBOT", "robot"),
        ("3 GOAL", "goal"),
        ("4 ERASE", "erase"),
        ("S SAVE", "save"),
        ("R RUN CBS", "run"),
    ]

    button_x = 8
    button_y = panel_y + 10

    # Six buttons must fit inside the 660px-wide window.
    button_width = 100
    button_height = 35
    button_gap = 8

    font_button = pygame.font.SysFont(
        "arial",
        13,
        bold=True
    )

    for label, mode in buttons:

        rect = pygame.Rect(
            button_x,
            button_y,
            button_width,
            button_height
        )

        # RUN CBS gets its own color
        if mode == "run":

            color = RUN_BUTTON_COLOR

        elif mode == current_mode:

            color = BUTTON_ACTIVE_COLOR

        else:

            color = BUTTON_COLOR

        pygame.draw.rect(
            screen,
            color,
            rect,
            border_radius=5
        )

        pygame.draw.rect(
            screen,
            DARK_GRAY,
            rect,
            1,
            border_radius=5
        )

        text = font_button.render(
            label,
            True,
            TEXT_COLOR
        )

        text_rect = text.get_rect(
            center=rect.center
        )

        screen.blit(
            text,
            text_rect
        )

        button_x += button_width + button_gap

    # --------------------------------------------------------
    # Information
    # --------------------------------------------------------

    font_info = pygame.font.SysFont(
        "arial",
        15
    )

    info_y = panel_y + 58

    info_text = (
        f"Mode: {current_mode.upper()}    "
        f"Obstacles: {len(obstacles)}    "
        f"Robots: {len(robots)}    "
        f"Goals: {len(goals)}"
    )

    text = font_info.render(
        info_text,
        True,
        TEXT_COLOR
    )

    screen.blit(
        text,
        (10, info_y)
    )

    # --------------------------------------------------------
    # Instructions
    # --------------------------------------------------------

    instruction_text = (
        "1-4: Mode    "
        "S: Save    "
        "R: Run CBS    "
        "C: Clear    "
        "Q / ESC: Quit"
    )

    text = font_info.render(
        instruction_text,
        True,
        DARK_GRAY
    )

    screen.blit(
        text,
        (10, info_y + 27)
    )

    # --------------------------------------------------------
    # Goal warning
    # --------------------------------------------------------

    missing_goals = [
        robot_id
        for robot_id in robots
        if robot_id not in goals
    ]

    if missing_goals:

        warning_text = (
            "Robot(s) without goals: "
            + ", ".join(
                str(robot_id)
                for robot_id in missing_goals
            )
        )

        text = font_info.render(
            warning_text,
            True,
            (200, 60, 60)
        )

        screen.blit(
            text,
            (10, info_y + 54)
        )

    else:

        ready_text = (
            "All robots have goals - ready to run CBS"
        )

        text = font_info.render(
            ready_text,
            True,
            (40, 140, 70)
        )

        screen.blit(
            text,
            (10, info_y + 54)
        )


# ============================================================
# GET GRID POSITION
# ============================================================

def get_grid_position(mouse_x, mouse_y):

    # Click outside grid
    if mouse_y >= GRID_HEIGHT:

        return None

    col = mouse_x // CELL_SIZE
    row = mouse_y // CELL_SIZE

    return row, col


# ============================================================
# SAVE SCENARIO
# ============================================================

def save_dynamic_scenario(obstacles, robots, goals):

    # --------------------------------------------------------
    # Check that every robot has a goal
    # --------------------------------------------------------

    missing_goals = [
        robot_id
        for robot_id in robots
        if robot_id not in goals
    ]

    if missing_goals:

        print()
        print("=" * 45)
        print("CANNOT SAVE SCENARIO")
        print("=" * 45)

        print(
            "The following robot(s) do not have goals:"
        )

        print(
            ", ".join(
                str(robot_id)
                for robot_id in missing_goals
            )
        )

        print("=" * 45)

        return False

    # --------------------------------------------------------
    # Create grid
    #
    # Editor uses:
    #     (row, col)
    #
    # Project uses:
    #     (x, y)
    #
    # Therefore:
    #     x = col
    #     y = row
    # --------------------------------------------------------

    grid = []

    for row in range(ROWS):

        current_row = []

        for col in range(COLS):

            if (row, col) in obstacles:

                current_row.append(1)

            else:

                current_row.append(0)

        grid.append(current_row)

    # --------------------------------------------------------
    # Create robot list
    # --------------------------------------------------------

    robot_data = []

    for robot_id, start in robots.items():

        start_row, start_col = start

        goal_row, goal_col = goals[robot_id]

        robot_data.append(
            {
                "id": robot_id,

                "start": [
                    start_col,
                    start_row
                ],

                "goal": [
                    goal_col,
                    goal_row
                ]
            }
        )

    # --------------------------------------------------------
    # Create final scenario
    # --------------------------------------------------------

    scenario = {
        "grid": grid,
        "robots": robot_data
    }

    # --------------------------------------------------------
    # Make sure scenarios folder exists
    # --------------------------------------------------------

    os.makedirs(
        "scenarios",
        exist_ok=True
    )

    # --------------------------------------------------------
    # File path
    # --------------------------------------------------------

    file_path = os.path.join(
        "scenarios",
        "dynamic.json"
    )

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

    with open(
        file_path,
        "w"
    ) as file:

        json.dump(
            scenario,
            file,
            indent=2
        )

    # --------------------------------------------------------
    # Terminal confirmation
    # --------------------------------------------------------

    print()
    print("=" * 45)
    print("SCENARIO SAVED SUCCESSFULLY")
    print("=" * 45)

    print(
        f"File: {file_path}"
    )

    print(
        f"Grid: {COLS} x {ROWS}"
    )

    print(
        f"Obstacles: {len(obstacles)}"
    )

    print(
        f"Robots: {len(robot_data)}"
    )

    print(
        f"Goals: {len(goals)}"
    )

    print("=" * 45)
    print()

    return True


# ============================================================
# RUN CBS
# ============================================================

def run_cbs(obstacles, robots, goals):

    print()
    print("=" * 45)
    print("RUN CBS REQUESTED")
    print("=" * 45)

    # --------------------------------------------------------
    # First save the current scenario
    # --------------------------------------------------------

    saved = save_dynamic_scenario(
        obstacles,
        robots,
        goals
    )

    # If saving failed, don't run CBS
    if not saved:

        print("CBS was not started.")
        print("=" * 45)

        return

    # --------------------------------------------------------
    # Run the existing main.py
    #
    # We pass dynamic.json explicitly so main.py uses
    # the custom scenario instead of simple.json.
    # --------------------------------------------------------

    scenario_path = os.path.join(
        "scenarios",
        "dynamic.json"
    )

    try:

        print("Starting CBS...")
        print(
            f"Scenario: {scenario_path}"
        )
        print()

        subprocess.Popen(
            [
                sys.executable,
                "main.py",
                scenario_path
            ]
        )

    except Exception as error:

        print()
        print("=" * 45)
        print("FAILED TO START CBS")
        print("=" * 45)
        print(error)
        print("=" * 45)


# ============================================================
# MAIN
# ============================================================

def main():

    pygame.init()

    screen = pygame.display.set_mode(
        (WIDTH, HEIGHT)
    )

    pygame.display.set_caption(
        "Dynamic Warehouse Editor"
    )

    clock = pygame.time.Clock()

    # --------------------------------------------------------
    # Data
    # --------------------------------------------------------

    obstacles = set()

    # robot_id -> (row, col)
    robots = {}

    # robot_id -> (row, col)
    goals = {}

    next_robot_id = 1

    # Current mode
    current_mode = "obstacle"

    # --------------------------------------------------------
    # Main loop
    # --------------------------------------------------------

    running = True

    while running:

        for event in pygame.event.get():

            # =================================================
            # WINDOW CLOSE
            # =================================================

            if event.type == pygame.QUIT:

                running = False

            # =================================================
            # MOUSE CLICK
            # =================================================

            elif event.type == pygame.MOUSEBUTTONDOWN:

                mouse_x, mouse_y = event.pos

                # ---------------------------------------------
                # Bottom panel
                # ---------------------------------------------

                if mouse_y >= GRID_HEIGHT:

                    # Button positions:
                    #
                    # 1 = x 8 - 108
                    # 2 = x 116 - 216
                    # 3 = x 224 - 324
                    # 4 = x 332 - 432
                    # 5 = x 440 - 540
                    # 6 = x 548 - 648

                    # -----------------------------------------
                    # SAVE button
                    # -----------------------------------------

                    if (
                        440 <= mouse_x <= 540
                        and GRID_HEIGHT + 10
                        <= mouse_y
                        <= GRID_HEIGHT + 45
                    ):

                        save_dynamic_scenario(
                            obstacles,
                            robots,
                            goals
                        )

                    # -----------------------------------------
                    # RUN CBS button
                    # -----------------------------------------

                    elif (
                        548 <= mouse_x <= 648
                        and GRID_HEIGHT + 10
                        <= mouse_y
                        <= GRID_HEIGHT + 45
                    ):

                        run_cbs(
                            obstacles,
                            robots,
                            goals
                        )

                    continue

                # ---------------------------------------------
                # Get clicked grid position
                # ---------------------------------------------

                position = get_grid_position(
                    mouse_x,
                    mouse_y
                )

                if position is None:

                    continue

                row, col = position

                # =================================================
                # OBSTACLE MODE
                # =================================================

                if current_mode == "obstacle":

                    # Cannot place obstacle on robot
                    if position in robots.values():

                        continue

                    # Cannot place obstacle on goal
                    if position in goals.values():

                        continue

                    # Toggle obstacle
                    if position in obstacles:

                        obstacles.remove(position)

                    else:

                        obstacles.add(position)

                # =================================================
                # ROBOT MODE
                # =================================================

                elif current_mode == "robot":

                    # Cannot place robot on obstacle
                    if position in obstacles:

                        continue

                    # Cannot place robot on another robot
                    if position in robots.values():

                        continue

                    # Cannot place robot on goal
                    if position in goals.values():

                        continue

                    # Add robot
                    robots[next_robot_id] = position

                    next_robot_id += 1

                # =================================================
                # GOAL MODE
                # =================================================

                elif current_mode == "goal":

                    # Cannot place goal on obstacle
                    if position in obstacles:

                        continue

                    # Cannot place goal on robot
                    if position in robots.values():

                        continue

                    # Cannot duplicate a goal
                    if position in goals.values():

                        continue

                    # Find first robot without a goal
                    robot_without_goal = None

                    for robot_id in robots:

                        if robot_id not in goals:

                            robot_without_goal = robot_id

                            break

                    # If every robot already has a goal
                    if robot_without_goal is None:

                        continue

                    # Assign goal
                    goals[
                        robot_without_goal
                    ] = position

                # =================================================
                # ERASE MODE
                # =================================================

                elif current_mode == "erase":

                    # ---------------------------------------------
                    # Erase obstacle
                    # ---------------------------------------------

                    if position in obstacles:

                        obstacles.remove(position)

                    # ---------------------------------------------
                    # Erase goal
                    # ---------------------------------------------

                    else:

                        goal_robot = None

                        for robot_id, goal in goals.items():

                            if goal == position:

                                goal_robot = robot_id

                                break

                        if goal_robot is not None:

                            del goals[goal_robot]

                        # -----------------------------------------
                        # Erase robot
                        # -----------------------------------------

                        else:

                            robot_to_delete = None

                            for (
                                robot_id,
                                robot_position
                            ) in robots.items():

                                if robot_position == position:

                                    robot_to_delete = robot_id

                                    break

                            if robot_to_delete is not None:

                                del robots[
                                    robot_to_delete
                                ]

                                # Also delete its goal
                                if robot_to_delete in goals:

                                    del goals[
                                        robot_to_delete
                                    ]

            # =================================================
            # KEYBOARD
            # =================================================

            elif event.type == pygame.KEYDOWN:

                # ---------------------------------------------
                # OBSTACLE MODE
                # ---------------------------------------------

                if event.key == pygame.K_1:

                    current_mode = "obstacle"

                # ---------------------------------------------
                # ROBOT MODE
                # ---------------------------------------------

                elif event.key == pygame.K_2:

                    current_mode = "robot"

                # ---------------------------------------------
                # GOAL MODE
                # ---------------------------------------------

                elif event.key == pygame.K_3:

                    current_mode = "goal"

                # ---------------------------------------------
                # ERASE MODE
                # ---------------------------------------------

                elif event.key == pygame.K_4:

                    current_mode = "erase"

                # ---------------------------------------------
                # SAVE
                # ---------------------------------------------

                elif event.key == pygame.K_s:

                    save_dynamic_scenario(
                        obstacles,
                        robots,
                        goals
                    )

                # ---------------------------------------------
                # RUN CBS
                # ---------------------------------------------

                elif event.key == pygame.K_r:

                    run_cbs(
                        obstacles,
                        robots,
                        goals
                    )

                # ---------------------------------------------
                # CLEAR
                # ---------------------------------------------

                elif event.key == pygame.K_c:

                    obstacles.clear()
                    robots.clear()
                    goals.clear()

                    next_robot_id = 1

                # ---------------------------------------------
                # QUIT
                # ---------------------------------------------

                elif (
                    event.key == pygame.K_q
                    or event.key == pygame.K_ESCAPE
                ):

                    running = False

        # =====================================================
        # DRAW
        # =====================================================

        draw_grid(
            screen,
            obstacles,
            robots,
            goals,
            current_mode
        )

        pygame.display.flip()

        clock.tick(60)

    # =========================================================
    # CLEANUP
    # =========================================================

    pygame.quit()

    sys.exit()


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    main()