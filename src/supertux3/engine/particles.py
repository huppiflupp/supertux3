"""Leichtgewichtiges Partikelsystem + schwebende Texte für „Juice"."""
from __future__ import annotations

import random

import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "grav", "life", "max_life",
                 "color", "r", "shrink", "drag")

    def __init__(self, x, y, vx, vy, grav, life, color, r, shrink=1.0, drag=1.0):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.grav = grav
        self.life = self.max_life = life
        self.color = color
        self.r = r
        self.shrink = shrink
        self.drag = drag

    def update(self, dt):
        self.vy += self.grav * dt
        self.vx *= self.drag
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0


class FloatText:
    __slots__ = ("x", "y", "text", "color", "life", "max_life", "font")

    def __init__(self, x, y, text, color, font, life=0.8):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.life = self.max_life = life
        self.font = font

    def update(self, dt):
        self.y -= 34 * dt
        self.life -= dt
        return self.life > 0


class Particles:
    def __init__(self):
        self.items: list[Particle] = []
        self.texts: list[FloatText] = []

    # --- Emitter -----------------------------------------------------
    def coin(self, x, y):
        for _ in range(8):
            a = random.uniform(0, 6.283)
            sp = random.uniform(40, 120)
            self.items.append(Particle(
                x, y, random.uniform(-40, 40), -abs(sp),
                420, random.uniform(0.3, 0.6),
                random.choice([(255, 244, 190), (255, 214, 70), (255, 255, 255)]),
                random.uniform(1.5, 3), shrink=0.9, drag=0.92))

    def stomp(self, x, y):
        for _ in range(14):
            self.items.append(Particle(
                x + random.uniform(-8, 8), y, random.uniform(-160, 160),
                random.uniform(-140, -20), 600, random.uniform(0.3, 0.7),
                random.choice([(245, 250, 255), (210, 220, 235), (200, 205, 215)]),
                random.uniform(2, 4), shrink=0.9, drag=0.9))

    def dust(self, x, y, n=6, tone=(226, 214, 190)):
        for _ in range(n):
            self.items.append(Particle(
                x + random.uniform(-6, 6), y, random.uniform(-70, 70),
                random.uniform(-50, -6), 320, random.uniform(0.2, 0.45),
                tone, random.uniform(1.5, 3), shrink=0.9, drag=0.9))

    def poof(self, x, y, color=(60, 66, 90), n=22):
        for _ in range(n):
            a = random.uniform(0, 6.283)
            sp = random.uniform(60, 240)
            self.items.append(Particle(
                x, y, random.uniform(-1, 1) * sp, random.uniform(-1, 1) * sp - 60,
                500, random.uniform(0.4, 0.9), color,
                random.uniform(2, 4.5), shrink=0.92, drag=0.93))

    def sparkle(self, x, y, color=(255, 236, 130), n=16):
        for _ in range(n):
            a = random.uniform(0, 6.283)
            sp = random.uniform(30, 130)
            import math
            self.items.append(Particle(
                x, y, math.cos(a) * sp, math.sin(a) * sp,
                80, random.uniform(0.4, 0.8), color,
                random.uniform(1.5, 3), shrink=0.9, drag=0.9))

    def text(self, x, y, s, color, font):
        self.texts.append(FloatText(x, y, s, color, font))

    # --- Update / Draw ----------------------------------------------
    def update(self, dt):
        self.items = [p for p in self.items if p.update(dt)]
        self.texts = [t for t in self.texts if t.update(dt)]

    def draw(self, surface, camera):
        ox, oy = camera.offset
        for p in self.items:
            k = max(0.0, p.life / p.max_life)
            r = max(1, p.r * (p.shrink + (1 - p.shrink) * k))
            a = int(255 * min(1.0, k * 1.6))
            d = int(r * 2)
            surf = pygame.Surface((d, d), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p.color, a), (d // 2, d // 2), int(r))
            surface.blit(surf, (int(p.x - ox - r), int(p.y - oy - r)))
        for t in self.texts:
            k = max(0.0, t.life / t.max_life)
            a = int(255 * min(1.0, k * 1.8))
            img = t.font.render(t.text, True, t.color)
            img.set_alpha(a)
            sh = t.font.render(t.text, True, (20, 20, 30))
            sh.set_alpha(a)
            rect = img.get_rect(center=(int(t.x - ox), int(t.y - oy)))
            surface.blit(sh, rect.move(2, 2))
            surface.blit(img, rect)

    def clear(self):
        self.items.clear()
        self.texts.clear()
