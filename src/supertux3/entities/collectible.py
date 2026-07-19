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


class GrowItem(Entity):
    """Schwebendes Wachstums-Item: macht kleinen Pengu groß."""

    def __init__(self, x: float, y: float, assets):
        img = assets.item_grow
        super().__init__(x, y, img.get_width(), img.get_height())
        self.img = img
        self.base_y = float(y)
        self.t = (x * 0.11) % (math.pi * 2)

    def update(self, dt: float, level) -> None:
        self.t += dt * 2.5
        self.y = self.base_y + math.sin(self.t) * 4.0

    def draw(self, surface: pygame.Surface, camera) -> None:
        ox, oy = camera.offset
        surface.blit(self.img, (round(self.x) - ox, round(self.y) - oy))


class FishItem(Entity):
    """Fisch-Powerup: verleiht die Wurffähigkeit."""

    def __init__(self, x, y, assets):
        img = assets.fish
        super().__init__(x, y, img.get_width(), img.get_height())
        self.img = img
        self.base_y = float(y)
        self.t = (x * 0.1) % (math.pi * 2)

    def update(self, dt, level):
        self.t += dt * 3.0
        self.y = self.base_y + math.sin(self.t) * 4.0

    def draw(self, surface, camera):
        ox, oy = camera.offset
        surface.blit(self.img, (round(self.x) - ox, round(self.y) - oy))


class FishRainItem(Entity):
    """Zeitlich begrenztes Powerup: löst den Fischregen aus."""

    def __init__(self, x, y, assets):
        img = assets.plane
        super().__init__(x, y, img.get_width(), img.get_height())
        self.img = img
        self.base_y = float(y)
        self.t = (x * 0.07) % (math.pi * 2)

    def update(self, dt, level):
        self.t += dt * 2.0
        self.y = self.base_y + math.sin(self.t) * 5.0

    def draw(self, surface, camera):
        ox, oy = camera.offset
        surface.blit(self.img, (round(self.x) - ox, round(self.y) - oy))


class Star(Entity):
    """Sammel-Stern (3 pro Level, für Bestwertung)."""

    def __init__(self, x: float, y: float, assets):
        img = assets.star
        super().__init__(x, y, img.get_width(), img.get_height())
        self.img = img
        self.base_y = float(y)
        self.t = (x * 0.09) % (math.pi * 2)

    def update(self, dt: float, level) -> None:
        self.t += dt * 3.0
        self.y = self.base_y + math.sin(self.t) * 5.0

    def draw(self, surface: pygame.Surface, camera) -> None:
        ox, oy = camera.offset
        import math as _m
        scale = 1.0 + 0.08 * _m.sin(self.t * 2)
        img = self.img
        if abs(scale - 1) > 0.01:
            w = max(1, int(img.get_width() * scale))
            h = max(1, int(img.get_height() * scale))
            img = pygame.transform.smoothscale(img, (w, h))
        surface.blit(img, (int(self.cx - img.get_width() / 2 - ox),
                           int(self.cy - img.get_height() / 2 - oy)))


class SecretDoor(Entity):
    """Versteckter Ausgang: führt in ein Geheimlevel (schimmerndes Portal)."""

    def __init__(self, x: float, y: float, secret_id: str = "secret1.json"):
        super().__init__(x, y - 40, 28, 40)
        self.secret_id = secret_id
        self.t = 0.0

    def update(self, dt: float, level) -> None:
        self.t += dt * 4.0

    def draw(self, surface: pygame.Surface, camera) -> None:
        ox, oy = camera.offset
        cx = int(self.cx - ox)
        cy = int(self.cy - oy)
        r = self.rect
        surf = pygame.Surface((r.w + 12, r.h + 12), pygame.SRCALPHA)
        for i, a in enumerate((60, 110, 200)):
            rr = (r.w // 2 + 6) - i * 4
            col = (150, 90, 220, a)
            pygame.draw.ellipse(surf, col, (surf.get_width() // 2 - rr,
                                            surf.get_height() // 2 - int(rr * 1.4),
                                            rr * 2, int(rr * 2.8)))
        surface.blit(surf, (cx - surf.get_width() // 2, cy - surf.get_height() // 2))
        # Funkeln
        for k in range(3):
            ang = self.t + k * 2.1
            sx = cx + int(math.cos(ang) * 10)
            sy = cy + int(math.sin(ang * 1.3) * 16)
            pygame.draw.circle(surface, (240, 220, 255), (sx, sy), 1)


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
