"""Boss „Frostkönig" + seine Eis-Projektile."""
from __future__ import annotations

import pygame

from .entity import Entity
from ..engine.animation import Animation
from ..settings import TILE


class IceBall(Entity):
    """Vom Boss geworfenes Eis-Projektil – verletzt den Spieler."""

    def __init__(self, x, y, vx, assets):
        super().__init__(x, y, 14, 14)
        self.vx = vx
        self.vy = -220.0
        self.img = assets.iceball
        self.t = 4.0

    def update(self, dt, level):
        self.vy += 1500 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.t -= dt
        if self.t <= 0 or self.y > level.height_px + 40:
            self.remove = True

    def draw(self, surface, camera):
        ox, oy = camera.offset
        surface.blit(self.img, (round(self.x) - ox, round(self.y) - oy))


class Boss(Entity):
    stompable = True
    is_boss = True

    def __init__(self, x, y, assets, variant="frost"):
        super().__init__(x - 32, y - 54, 56, 54)
        self.assets = assets
        self.variant = variant
        walk = assets.boss["walk"]
        hurt = assets.boss["hurt"][0]
        if variant == "shadow":
            walk = [self._tint(f, (170, 120, 220)) for f in walk]
            hurt = self._tint(hurt, (170, 120, 220))
        self.walk = Animation(walk, fps=4 if variant == "frost" else 6)
        self.hurt_img = hurt
        self.hp = 3 if variant == "frost" else 4
        self.max_hp = self.hp
        self.invuln = 0.0
        self.defeated = False
        self.defeat_t = 1.6
        self.facing = -1
        self.jump_t = 2.2
        self.throw_t = 1.6
        self.hurt_flash = 0.0

    @staticmethod
    def _tint(surf, color):
        out = surf.copy()
        out.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
        return out

    @property
    def speed(self):
        base = 70.0 if self.variant == "frost" else 92.0
        return base + (self.max_hp - self.hp) * 24.0   # schneller pro Treffer

    def update(self, dt, level):
        if self.defeated:
            self.vy += 1400 * dt
            self.y += self.vy * dt
            self.defeat_t -= dt
            if self.defeat_t <= 0:
                self.remove = True
            return

        self.invuln = max(0.0, self.invuln - dt)
        self.hurt_flash = max(0.0, self.hurt_flash - dt)

        self.vx = self.speed * self.facing
        self.apply_gravity(dt)
        self.move_and_collide(level.tilemap, dt)
        if self.vx == 0:
            self.facing *= -1

        # springen
        self.jump_t -= dt
        if self.jump_t <= 0 and self.on_ground:
            self.vy = -560
            self.jump_t = 2.2

        # werfen (Richtung Spieler)
        self.throw_t -= dt
        if self.throw_t <= 0:
            base = 1.4 if self.variant == "shadow" else 1.8
            self.throw_t = max(0.7, base - (self.max_hp - self.hp) * 0.3)
            px = level.player.cx
            d = 1 if px > self.cx else -1
            level.projectiles.append(
                IceBall(self.cx, self.y + 6, d * 150.0, self.assets))
            level.game.audio.play("throw")

        self.walk.update(dt)

    def hit(self) -> bool:
        """Ein Stampf-Treffer. True, wenn er zählt."""
        if self.invuln > 0 or self.defeated:
            return False
        self.hp -= 1
        self.invuln = 1.0
        self.hurt_flash = 0.4
        if self.hp <= 0:
            self.defeated = True
            self.vy = -260
        return True

    def draw(self, surface, camera):
        ox, oy = camera.offset
        if self.invuln > 0 and int(self.invuln * 20) % 2 == 0:
            return
        img = self.hurt_img if (self.hurt_flash > 0 or self.defeated) else self.walk.image
        if self.facing > 0:
            img = pygame.transform.flip(img, True, self.defeated)
        elif self.defeated:
            img = pygame.transform.flip(img, False, True)
        surface.blit(img, (round(self.x) - (img.get_width() - self.w) // 2 - ox,
                           self.rect.bottom - img.get_height() - oy))
