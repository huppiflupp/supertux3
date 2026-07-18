"""Gegner: der „Schneeball" – ein einfacher laufender Gegner.

Läuft hin und her, dreht an Wänden und Abgründen um. Wird er von oben
gestampft, wird er platt gedrückt und verschwindet.
"""
from __future__ import annotations

import pygame

from .entity import Entity
from ..engine.animation import Animation
from ..settings import TILE

SNOW_W, SNOW_H = 16, 14
SPEED = 34.0


class Snowball(Entity):
    def __init__(self, x: float, y: float, assets):
        super().__init__(x, y, SNOW_W, SNOW_H)
        self.walk = Animation(assets.snowball["walk"], fps=6)
        self.flat = assets.snowball["flat"][0]
        self.facing = -1
        self.squashed = False
        self.squash_t = 0.0

    def update(self, dt: float, level) -> None:
        if self.squashed:
            self.squash_t -= dt
            if self.squash_t <= 0:
                self.remove = True
            return

        self.vx = SPEED * self.facing
        self.apply_gravity(dt)
        self.move_and_collide(level.tilemap, dt)

        tm = level.tilemap
        if self.vx == 0:                      # gegen Wand gelaufen
            self.facing *= -1
        elif self.on_ground:                  # Abgrund voraus? -> umdrehen
            ahead = self.rect.right + 1 if self.facing > 0 else self.rect.left - 1
            tx = int(ahead // TILE)
            ty = int((self.rect.bottom + 1) // TILE)
            if not tm.is_solid(tx, ty):
                self.facing *= -1

        self.walk.update(dt)

    def stomp(self) -> None:
        self.squashed = True
        self.squash_t = 0.4
        self.vx = 0.0

    def draw(self, surface: pygame.Surface, camera) -> None:
        ox, oy = camera.offset
        if self.squashed:
            img = self.flat
            surface.blit(img, (round(self.x) - ox, self.rect.bottom - img.get_height() - oy))
        else:
            img = self.walk.image
            if self.facing > 0:
                img = pygame.transform.flip(img, True, False)
            surface.blit(img, (round(self.x) - (img.get_width() - SNOW_W) // 2 - ox,
                               self.rect.bottom - img.get_height() - oy))
