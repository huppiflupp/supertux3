"""Generisches Projektil (Gegner-Ball, geworfener/regnender Fisch)."""
from __future__ import annotations

import pygame

from .entity import Entity


class Projectile(Entity):
    def __init__(self, x, y, vx, vy, img, grav=1200.0, life=4.0, spin=False):
        w, h = img.get_size()
        super().__init__(x, y, w, h)
        self.vx, self.vy = vx, vy
        self.img = img
        self.grav = grav
        self.life = life
        self.spin = spin
        self.angle = 0.0

    def update(self, dt, level):
        self.vy += self.grav * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        if self.spin:
            self.angle = (self.angle - 640 * dt) % 360
        if self.life <= 0 or self.y > level.height_px + 80 \
                or self.x < -80 or self.x > level.width_px + 80:
            self.remove = True

    def draw(self, surface, camera):
        ox, oy = camera.offset
        img = self.img
        if self.vx < 0 and not self.spin:
            img = pygame.transform.flip(img, True, False)
        if self.spin and int(self.angle) != 0:
            img = pygame.transform.rotate(img, self.angle)
        surface.blit(img, (round(self.x) - ox, round(self.y) - oy))
