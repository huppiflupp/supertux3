"""Gegner: Schneeball (Läufer), Flieger (Sinus-Flug), Stachler (nicht stampfbar)."""
from __future__ import annotations

import math

import pygame

from .entity import Entity
from ..engine.animation import Animation
from ..settings import TILE


class _Walker(Entity):
    """Gemeinsame Basis für Boden-Gegner: laufen, an Wand/Abgrund umdrehen."""
    speed = 68.0

    def _patrol(self, dt, level):
        self.vx = self.speed * self.facing
        self.apply_gravity(dt)
        self.move_and_collide(level.tilemap, dt)
        tm = level.tilemap
        if self.vx == 0:                       # Wand
            self.facing *= -1
        elif self.on_ground:                   # Abgrund voraus?
            ahead = self.rect.right + 1 if self.facing > 0 else self.rect.left - 1
            tx = int(ahead // TILE)
            ty = int((self.rect.bottom + 1) // TILE)
            if not tm.is_solid(tx, ty):
                self.facing *= -1


class Snowball(_Walker):
    stompable = True
    speed = 68.0

    def __init__(self, x, y, assets):
        super().__init__(x, y, 32, 28)
        self.walk = Animation(assets.snowball["walk"], fps=6)
        self.flat = assets.snowball["flat"][0]
        self.facing = -1
        self.squashed = False
        self.squash_t = 0.0

    def update(self, dt, level):
        if self.squashed:
            self.squash_t -= dt
            if self.squash_t <= 0:
                self.remove = True
            return
        self._patrol(dt, level)
        self.walk.update(dt)

    def stomp(self):
        self.squashed = True
        self.squash_t = 0.4
        self.vx = 0.0

    def draw(self, surface, camera):
        ox, oy = camera.offset
        if self.squashed:
            img = self.flat
            surface.blit(img, (round(self.x) - ox, self.rect.bottom - img.get_height() - oy))
        else:
            img = self.walk.image
            if self.facing > 0:
                img = pygame.transform.flip(img, True, False)
            surface.blit(img, (round(self.x) - (img.get_width() - self.w) // 2 - ox,
                               self.rect.bottom - img.get_height() - oy))


class Spiky(_Walker):
    """Stachler – kann NICHT gestampft werden (Kontakt verletzt immer)."""
    stompable = False
    speed = 52.0

    def __init__(self, x, y, assets):
        super().__init__(x, y, 30, 28)
        self.walk = Animation(assets.spiky, fps=7)
        self.facing = -1

    def update(self, dt, level):
        self._patrol(dt, level)
        self.walk.update(dt)

    def draw(self, surface, camera):
        ox, oy = camera.offset
        img = self.walk.image
        if self.facing > 0:
            img = pygame.transform.flip(img, True, False)
        surface.blit(img, (round(self.x) - (img.get_width() - self.w) // 2 - ox,
                           self.rect.bottom - img.get_height() - oy))


class Flyer(Entity):
    """Flieger – schwebt in einer Sinuswelle, ist stampfbar."""
    stompable = True

    def __init__(self, x, y, assets, patrol=6):
        super().__init__(x, y, 30, 22)
        self.fly = Animation(assets.flyer, fps=8)
        self.origin_x = float(x)
        self.base_y = float(y)
        self.range = patrol * TILE
        self.speed = 60.0
        self.facing = -1
        self.t = (x * 0.1) % (math.pi * 2)
        self.squashed = False
        self.squash_t = 0.0

    def update(self, dt, level):
        if self.squashed:
            self.squash_t -= dt
            self.vy += 900 * dt
            self.y += self.vy * dt
            if self.squash_t <= 0:
                self.remove = True
            return
        self.x += self.speed * self.facing * dt
        if abs(self.x - self.origin_x) > self.range:
            self.facing *= -1
            self.x = self.origin_x + self.range * (1 if self.facing < 0 else -1)
        self.t += dt * 3.0
        self.y = self.base_y + math.sin(self.t) * 12.0
        self.fly.update(dt)

    def stomp(self):
        self.squashed = True
        self.squash_t = 0.5
        self.vy = 40.0

    def draw(self, surface, camera):
        ox, oy = camera.offset
        img = self.fly.image
        if self.facing > 0:
            img = pygame.transform.flip(img, True, False)
        if self.squashed:
            img = pygame.transform.flip(img, False, True)
        surface.blit(img, (round(self.x) - (img.get_width() - self.w) // 2 - ox,
                           round(self.y) - (img.get_height() - self.h) // 2 - oy))
