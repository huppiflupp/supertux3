"""Interaktive Objekte: bewegliche Plattform, Sprungfeder, Checkpoint."""
from __future__ import annotations

import pygame

from .entity import Entity
from ..settings import TILE


def _plank_image(w: int, h: int) -> pygame.Surface:
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (150, 106, 64), (0, 0, w, h), border_radius=5)
    pygame.draw.rect(s, (176, 130, 84), (2, 2, w - 4, h // 2 - 1), border_radius=4)
    pygame.draw.rect(s, (120, 84, 50), (0, h - 4, w, 4), border_radius=3)
    for x in range(8, w - 4, 18):
        pygame.draw.line(s, (120, 84, 50), (x, 3), (x, h - 4), 1)
    pygame.draw.rect(s, (90, 62, 38), (0, 0, w, h), width=2, border_radius=5)
    return s


class MovingPlatform(Entity):
    solid = True

    def __init__(self, x, y, x2, y2, w_tiles=3, speed=60.0):
        w = int(w_tiles * TILE)
        h = 16
        super().__init__(x, y, w, h)
        self.ax, self.ay = float(x), float(y)
        self.bx, self.by = float(x2), float(y2)
        self.speed = speed
        self.dir = 1
        self.s = 0.0
        import math
        self.dist = max(1.0, math.hypot(self.bx - self.ax, self.by - self.ay))
        self.dx = 0.0
        self.dy = 0.0
        self.img = _plank_image(w, h)

    def update(self, dt, level):
        ox, oy = self.x, self.y
        self.s += self.dir * (self.speed / self.dist) * dt
        if self.s >= 1.0:
            self.s = 1.0
            self.dir = -1
        elif self.s <= 0.0:
            self.s = 0.0
            self.dir = 1
        self.x = self.ax + (self.bx - self.ax) * self.s
        self.y = self.ay + (self.by - self.ay) * self.s
        self.dx = self.x - ox
        self.dy = self.y - oy

    def draw(self, surface, camera):
        ox, oy = camera.offset
        surface.blit(self.img, (round(self.x) - ox, round(self.y) - oy))


class Spring(Entity):
    def __init__(self, x, y, assets):
        frames = assets.spring
        w, h = frames[0].get_width(), frames[0].get_height()
        super().__init__(x, y - h, w, h)
        self.frames = frames
        self.compress = 0.0

    def update(self, dt, level):
        self.compress = max(0.0, self.compress - dt * 4)

    def trigger(self):
        self.compress = 1.0

    def draw(self, surface, camera):
        ox, oy = camera.offset
        img = self.frames[1] if self.compress > 0.4 and len(self.frames) > 1 else self.frames[0]
        surface.blit(img, (round(self.x) - ox, self.rect.bottom - img.get_height() - oy))


class Box(Entity):
    """Zerstörbare ?-Box: von unten anschlagen -> zufälliges Item."""
    solid = True

    def __init__(self, x, y, assets):
        img = assets.box
        super().__init__(x, y, img.get_width(), img.get_height())
        self.img = img
        self.bump = 0.0

    def update(self, dt, level):
        self.bump = max(0.0, self.bump - dt * 6)

    def hit(self):
        self.bump = 1.0

    def draw(self, surface, camera):
        ox, oy = camera.offset
        off = int(self.bump * 5)
        surface.blit(self.img, (round(self.x) - ox, round(self.y) - off - oy))


class Checkpoint(Entity):
    def __init__(self, x, y, assets):
        frames = assets.checkpoint
        w, h = frames[0].get_width(), frames[0].get_height()
        super().__init__(x, y - h, w, h)
        self.frames = frames
        self.active = False

    def update(self, dt, level):
        pass

    def draw(self, surface, camera):
        ox, oy = camera.offset
        img = self.frames[1] if self.active and len(self.frames) > 1 else self.frames[0]
        surface.blit(img, (round(self.x) - ox, round(self.y) - oy))
