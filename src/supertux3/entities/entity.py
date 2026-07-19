"""Basis-Entity mit Achsen-getrennter AABB-Kachelkollision."""
from __future__ import annotations

import pygame

from ..settings import GRAVITY, MAX_FALL_SPEED
from ..world.tilemap import SLOPE_DIR


class Entity:
    def __init__(self, x: float, y: float, w: int, h: int):
        self.x = float(x)
        self.y = float(y)
        self.w = int(w)
        self.h = int(h)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing = 1          # 1 = rechts, -1 = links
        self.dead = False
        self.remove = False      # aus der Welt entfernen

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.w, self.h)

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def apply_gravity(self, dt: float) -> None:
        self.vy = min(self.vy + GRAVITY * dt, MAX_FALL_SPEED)

    def move_and_collide(self, tilemap, dt: float, extra_solids=()) -> None:
        """Bewegt die Entity und löst Kollisionen achsenweise auf.

        extra_solids: zusätzliche feste Rechtecke (z.B. bewegliche Plattformen).
        """
        # --- horizontal ---
        was_ground = self.on_ground
        self.x += self.vx * dt
        rect = self.rect
        solids = list(tilemap.solid_rects_around(rect)) + list(extra_solids)
        for solid in solids:
            if rect.colliderect(solid):
                # Auto-Step: niedrige Kanten (<=10px, z.B. Schräge->Plateau)
                # hochsteigen statt blockieren, wenn wir am Boden sind.
                if was_ground and rect.top < solid.top < rect.bottom \
                        and rect.bottom - solid.top <= 16:
                    self.y -= (rect.bottom - solid.top)
                    rect = self.rect
                    continue
                if self.vx > 0:
                    rect.right = solid.left
                elif self.vx < 0:
                    rect.left = solid.right
                self.x = float(rect.x)
                self.vx = 0.0

        # --- vertikal ---
        self.on_ground = False
        self.y += self.vy * dt
        rect = self.rect
        solids = list(tilemap.solid_rects_around(rect)) + list(extra_solids)
        for solid in solids:
            if rect.colliderect(solid):
                if self.vy > 0:
                    rect.bottom = solid.top
                    self.on_ground = True
                elif self.vy < 0:
                    rect.top = solid.bottom
                self.y = float(rect.y)
                self.vy = 0.0

        # --- Schrägen (nicht AABB-solide, per Oberflächenhöhe aufgelöst) ---
        if self.vy >= 0:
            rect = self.rect
            t = tilemap.tile
            cx = rect.centerx
            tx = cx // t
            for ty in range(rect.top // t, rect.bottom // t + 2):
                d = SLOPE_DIR.get(tilemap.tile_id(tx, ty), 0)
                if d == 0:
                    continue
                localx = cx - tx * t
                surf = (ty + 1) * t - localx if d > 0 else ty * t + localx
                surf = max(ty * t, min((ty + 1) * t, surf))
                if surf - 2 <= rect.bottom <= (ty + 1) * t + 6:
                    self.y = float(surf - self.h)
                    self.vy = 0.0
                    self.on_ground = True
                    break

    # von Unterklassen überschrieben
    def update(self, dt: float, level) -> None:
        pass

    def draw(self, surface: pygame.Surface, camera) -> None:
        pass
