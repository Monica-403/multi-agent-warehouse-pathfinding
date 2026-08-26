"""
simulation/animation.py
Main simulation loop: runs the PyGame window, updates the playback clock,
and renders robots moving along their CBS-planned paths.
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
        print("Cannot visualize: no collision-free solution was found.")
        return

    # Attach the final paths to each robot object for easy position lookup
    for robot in robots:
        robot.path = result.paths[robot.id]

    max_time = max(robot.finish_time() for robot in robots)
    total_cost = sum(robot.path_cost() for robot in robots)

    renderer = Renderer(grid, cell_size=cell_size)
    controller = PlaybackController(max_time=max_time, fps=30)
    clock = pygame.time.Clock()

    running = True
    while running:
        dt = clock.tick(renderer_fps := 30) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
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
            collision_free=True,  # CBS guarantees this when result.success is True
            num_robots=len(robots),
        )
        renderer.flip()

    pygame.quit()