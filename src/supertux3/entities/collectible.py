"""Sammelobjekte: Münze und Zielfahne."""
from __future__ import annotations

import math

import pygame

from .entity import Entity
from ..engine.animation import Animation

COIN_W = COIN_H = 24


class Coin(Entity):
    def __init__(self, x: float, y: float, assets):
        super().__init__(x, y, COIN_W, COIN_H)
        self.spin = Animation(assets.coin, fps=10)
        self.base_y = float(y)
        self.t = (x * 0.13) % (math.pi * 2)   # Phase aus Position -> versetztes Wippen

    def update(self, dt: float, level) -> None:
        self.spin.update(dt)
        self.t += dt * 3.0
        self.y = self.base_y + math.sin(self.t) * 4.0

    def draw(self, surface: pygame.Surface, camera) -> None:
        ox, oy = camera.offset
        surface.blit(self.spin.image, (round(self.x) - ox, round(self.y) - oy))


class Goal(Entity):
    """Zielfahne am Levelende."""

    def __init__(self, x: float, y: float, assets):
        img = assets.props["flag"]
        super().__init__(x, y - img.get_height(), img.get_width(), img.get_height())
        self.img = img

    def update(self, dt: float, level) -> None:
        pass

    def draw(self, surface: pygame.Surface, camera) -> None:
        ox, oy = camera.offset
        surface.blit(self.img, (round(self.x) - ox, round(self.y) - oy))
