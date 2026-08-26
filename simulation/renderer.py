"""
simulation/renderer.py
Draws the warehouse grid, obstacles, robots, goals, and metrics panel.
"""

import pygame
from typing import List, Tuple
from environment.grid import Grid
from environment.robot import Robot

# Colors
COLOR_BG = (245, 245, 245)
COLOR_FREE = (255, 255, 255)
COLOR_OBSTACLE = (60, 60, 60)
COLOR_GRID_LINE = (210, 210, 210)
COLOR_TEXT = (20, 20, 20)
COLOR_PANEL_BG = (30, 30, 40)
COLOR_PANEL_TEXT = (220, 220, 225)
COLOR_SAFE = (80, 220, 120)
COLOR_WARN = (240, 200, 80)

ROBOT_COLORS = [
    (231, 76, 60), (52, 152, 219), (46, 204, 113), (241, 196, 15),
    (155, 89, 182), (230, 126, 34), (26, 188, 156), (149, 165, 166),
    (192, 57, 43), (41, 128, 185), (39, 174, 96), (243, 156, 18),
    (142, 68, 173), (211, 84, 0), (22, 160, 133), (127, 140, 141),
]


def robot_color(robot_id: int) -> Tuple[int, int, int]:
    return ROBOT_COLORS[robot_id % len(ROBOT_COLORS)]


class Renderer:
    # Minimum window width so panel text always has room, regardless of grid size
    MIN_WINDOW_WIDTH = 620
    PANEL_LINE_HEIGHT = 24
    PANEL_PADDING_TOP = 14
    PANEL_PADDING_BOTTOM = 14

    def __init__(self, grid: Grid, cell_size: int = 40):
        self.grid = grid
        self.cell_size = cell_size

        self.grid_width_px = grid.width * cell_size
        self.grid_height_px = grid.height * cell_size

        # Panel now has 7 stacked lines -> compute height dynamically
        num_panel_lines = 7
        self.panel_height = (
            self.PANEL_PADDING_TOP
            + self.PANEL_PADDING_BOTTOM
            + num_panel_lines * self.PANEL_LINE_HEIGHT
        )

        self.width = max(self.grid_width_px, self.MIN_WINDOW_WIDTH)
        self.height = self.grid_height_px + self.panel_height

        pygame.init()
        pygame.display.set_caption("Multi-Agent Warehouse Pathfinding (CBS)")
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

        self.font = pygame.font.SysFont("consolas", 16)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self.font_bold = pygame.font.SysFont("consolas", 18, bold=True)

    def cell_to_px(self, x: int, y: int) -> Tuple[int, int]:
        return x * self.cell_size, y * self.cell_size

    def draw_grid(self):
        self.screen.fill(COLOR_BG)
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                px, py = self.cell_to_px(x, y)
                rect = pygame.Rect(px, py, self.cell_size, self.cell_size)
                if self.grid.data[y][x] == 1:
                    pygame.draw.rect(self.screen, COLOR_OBSTACLE, rect)
                else:
                    pygame.draw.rect(self.screen, COLOR_FREE, rect)
                pygame.draw.rect(self.screen, COLOR_GRID_LINE, rect, 1)

        # Fill any extra width beyond the grid (when window is wider than grid) with panel color
        if self.width > self.grid_width_px:
            extra_rect = pygame.Rect(self.grid_width_px, 0, self.width - self.grid_width_px, self.grid_height_px)
            pygame.draw.rect(self.screen, COLOR_BG, extra_rect)

    def draw_goals(self, robots: List[Robot]):
        for robot in robots:
            gx, gy = robot.goal
            px, py = self.cell_to_px(gx, gy)
            color = robot_color(robot.id)
            pygame.draw.rect(
                self.screen, color,
                pygame.Rect(px + 4, py + 4, self.cell_size - 8, self.cell_size - 8),
                width=3,
            )

    def draw_robots(self, robots: List[Robot], current_time: int):
        for robot in robots:
            x, y = robot.position_at(current_time)
            px, py = self.cell_to_px(x, y)
            center = (px + self.cell_size // 2, py + self.cell_size // 2)
            radius = self.cell_size // 2 - 4
            color = robot_color(robot.id)

            pygame.draw.circle(self.screen, color, center, radius)
            pygame.draw.circle(self.screen, (0, 0, 0), center, radius, 2)

            label = self.font_small.render(str(robot.id), True, (255, 255, 255))
            label_rect = label.get_rect(center=center)
            self.screen.blit(label, label_rect)

    def draw_panel(self, current_time: int, max_time: int, playing: bool, speed: float,
                    conflicts_detected: int, total_cost: int, makespan: int,
                    collision_free: bool, num_robots: int):
        panel_rect = pygame.Rect(0, self.grid_height_px, self.width, self.panel_height)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect)

        y = self.grid_height_px + self.PANEL_PADDING_TOP
        x = 16

        lines = [
            (f"Robots: {num_robots}    Time: {current_time} / {max_time}    "
             f"Status: {'PLAYING' if playing else 'PAUSED'}    Speed: {speed:.1f}x", self.font),
            (f"Conflicts Detected/Resolved: {conflicts_detected}", self.font),
            (f"Total Path Cost: {total_cost}    Makespan: {makespan}", self.font),
            ("Controls: SPACE=play/pause  R=restart  .=step fwd  ,=step back  UP/DOWN=speed",
             self.font_small),
        ]

        for text, font in lines:
            surf = font.render(text, True, COLOR_PANEL_TEXT)
            self.screen.blit(surf, (x, y))
            y += self.PANEL_LINE_HEIGHT

        y += 6
        status_text = "COLLISION FREE - OK" if collision_free else "CHECKING..."
        status_color = COLOR_SAFE if collision_free else COLOR_WARN
        status_surf = self.font_bold.render(status_text, True, status_color)
        self.screen.blit(status_surf, (x, y))

    def flip(self):
        pygame.display.flip()