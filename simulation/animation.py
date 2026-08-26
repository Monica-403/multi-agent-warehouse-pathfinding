"""
simulation/animation.py
Main simulation loop: runs the PyGame window, updates the playback clock,
and renders robots moving along their CBS-planned paths. Also handles the
case where CBS fails to find a collision-free solution.
"""

import pygame
from typing import List
from environment.grid import Grid
from environment.robot import Robot
from algorithms.cbs import CBSResult
from simulation.renderer import Renderer
from simulation.controls import PlaybackController


def run_simulation(grid: Grid, robots: List[Robot], result: CBSResult, cell_size: int = 40):
    if not result.success:
        run_failure_screen(grid, robots, result, cell_size)
        return

    for robot in robots:
        robot.path = result.paths[robot.id]

    max_time = max(robot.finish_time() for robot in robots)
    total_cost = sum(robot.path_cost() for robot in robots)

    renderer = Renderer(grid, cell_size=cell_size)
    controller = PlaybackController(max_time=max_time, fps=30)
    clock = pygame.time.Clock()

    running = True
    while running:
        dt = clock.tick(30) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False
            controller.handle_event(event)

        controller.update(dt)

        renderer.draw_grid()
        renderer.draw_goals(robots)
        renderer.draw_robots(robots, controller.current_time)
        renderer.draw_panel(
            current_time=controller.current_time,
            max_time=max_time,
            playing=controller.playing,
            speed=controller.speed,
            conflicts_detected=result.conflicts_detected,
            total_cost=total_cost,
            makespan=max_time,
            collision_free=True,
            num_robots=len(robots),
        )
        renderer.flip()

    pygame.quit()


def run_failure_screen(grid: Grid, robots: List[Robot], result: CBSResult, cell_size: int = 40):
    """
    Opens a PyGame window explaining that no collision-free solution was found,
    instead of silently exiting to console only. Still shows the warehouse
    layout and robot start/goal positions so the user can see WHY it might
    have failed (e.g. too many robots, not enough free space, blocked paths).
    """
    renderer = Renderer(grid, cell_size=cell_size)
    clock = pygame.time.Clock()

    font_big = pygame.font.SysFont("consolas", 26, bold=True)
    font_med = pygame.font.SysFont("consolas", 16)

    running = True
    while running:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False

        renderer.draw_grid()
        # Draw goals + robots at their starting positions (t=0) since no path exists
        renderer.draw_goals(robots)
        for robot in robots:
            x, y = robot.start
            px, py = renderer.cell_to_px(x, y)
            center = (px + renderer.cell_size // 2, py + renderer.cell_size // 2)
            radius = renderer.cell_size // 2 - 4
            pygame.draw.circle(renderer.screen, (150, 150, 150), center, radius)
            pygame.draw.circle(renderer.screen, (0, 0, 0), center, radius, 2)
            label = renderer.font_small.render(str(robot.id), True, (255, 255, 255))
            renderer.screen.blit(label, label.get_rect(center=center))

        # Panel: failure message + diagnostics
        panel_rect = pygame.Rect(0, renderer.grid_height_px, renderer.width, renderer.panel_height)
        pygame.draw.rect(renderer.screen, (60, 20, 20), panel_rect)

        y = renderer.grid_height_px + 14
        title = font_big.render("NO COLLISION-FREE SOLUTION FOUND", True, (255, 100, 100))
        renderer.screen.blit(title, (16, y))
        y += 34

        info_lines = [
            f"Robots: {len(robots)}",
            f"Conflicts encountered before giving up: {result.conflicts_detected}",
            f"CBS nodes expanded: {result.nodes_expanded}",
            f"Search time: {result.planning_time:.3f}s",
            "Possible causes: too many robots for available space, an unreachable",
            "goal (blocked by obstacles), or the CBS node/time limit was hit.",
            "Press Q or ESC to close.",
        ]
        for line in info_lines:
            surf = font_med.render(line, True, (230, 210, 210))
            renderer.screen.blit(surf, (16, y))
            y += 20

        renderer.flip()

    pygame.quit()