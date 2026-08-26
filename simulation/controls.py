"""
simulation/controls.py
Playback controller: manages simulation clock, play/pause state, and speed.
"""

import pygame


class PlaybackController:
    def __init__(self, max_time: int, fps: int = 30):
        self.max_time = max_time
        self.fps = fps
        self.current_time = 0
        self.playing = True
        self.speed = 1.0          # simulation steps per second
        self._accumulator = 0.0

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.playing = not self.playing
            elif event.key == pygame.K_r:
                self.current_time = 0
                self.playing = True
            elif event.key == pygame.K_PERIOD:  # step forward
                self.playing = False
                self.current_time = min(self.current_time + 1, self.max_time)
            elif event.key == pygame.K_COMMA:  # step backward
                self.playing = False
                self.current_time = max(self.current_time - 1, 0)
            elif event.key == pygame.K_UP:
                self.speed = min(self.speed + 0.5, 10.0)
            elif event.key == pygame.K_DOWN:
                self.speed = max(self.speed - 0.5, 0.25)

    def update(self, dt: float):
        """dt = seconds elapsed since last frame."""
        if not self.playing:
            return
        self._accumulator += dt * self.speed
        while self._accumulator >= 1.0:
            self._accumulator -= 1.0
            if self.current_time < self.max_time:
                self.current_time += 1
            else:
                self.playing = False  # auto-pause at the end