"""Einfache Frame-Animation."""
from __future__ import annotations

import pygame


class Animation:
    """Spielt eine Liste von Frames mit fester Bildrate ab."""

    def __init__(self, frames: list[pygame.Surface], fps: float = 10.0, loop: bool = True):
        assert frames, "Animation braucht mindestens einen Frame"
        self.frames = frames
        self.frame_time = 1.0 / fps if fps > 0 else 1e9
        self.loop = loop
        self.timer = 0.0
        self.index = 0
        self.finished = False

    def reset(self) -> None:
        self.timer = 0.0
        self.index = 0
        self.finished = False

    def update(self, dt: float) -> None:
        if self.finished:
            return
        self.timer += dt
        while self.timer >= self.frame_time:
            self.timer -= self.frame_time
            self.index += 1
            if self.index >= len(self.frames):
                if self.loop:
                    self.index = 0
                else:
                    self.index = len(self.frames) - 1
                    self.finished = True
                    break

    @property
    def image(self) -> pygame.Surface:
        return self.frames[self.index]
