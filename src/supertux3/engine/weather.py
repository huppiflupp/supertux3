"""Dynamische Wetter-Effekte + Wind.

Ein Level kann `weather` (rain|snow|fog|none) und `wind` (px/s^2, +rechts /
-links) setzen. Der Wind wird auf die Horizontalgeschwindigkeit des Spielers
addiert (weiter/kürzer springen je Richtung); die Partikel driften mit dem Wind.
Alles bildschirm-fest gezeichnet und mit dem Wind versetzt.
"""
from __future__ import annotations

import random

import pygame

from ..settings import VIRTUAL_W, VIRTUAL_H


class Weather:
    def __init__(self, kind: str = "none", wind: float = 0.0):
        self.kind = kind or "none"
        self.wind = float(wind)
        self.t = 0.0
        rng = random.Random(0xC0FFEE ^ hash(self.kind) & 0xFFFF)
        n = {"rain": 160, "snow": 90}.get(self.kind, 0)
        # (x, y, speed, phase/size)
        self.parts = [(rng.uniform(0, VIRTUAL_W), rng.uniform(0, VIRTUAL_H),
                       rng.uniform(0.7, 1.3), rng.uniform(0, 6.28)) for _ in range(n)]
        # Nebelbänder
        self.fog = [(rng.uniform(0, VIRTUAL_W), rng.uniform(VIRTUAL_H * 0.3, VIRTUAL_H),
                     rng.uniform(120, 240), rng.uniform(8, 22)) for _ in range(4)] \
            if self.kind == "fog" else []
        self._rain = pygame.Surface((3, 12), pygame.SRCALPHA)

    def update(self, dt: float):
        self.t += dt

    # --- Zeichnen (Vordergrund-Overlay) ------------------------------
    def draw(self, surface: pygame.Surface):
        if self.kind == "rain":
            self._draw_rain(surface)
        elif self.kind == "snow":
            self._draw_snow(surface)
        elif self.kind == "fog":
            self._draw_fog(surface)

    def _draw_rain(self, surface):
        wind = self.wind
        dx = max(-14, min(14, wind * 0.02))     # Schräglage aus Wind
        for i, (x, y, sp, ph) in enumerate(self.parts):
            fall = 520 * sp
            yy = (y + (self.t * fall)) % (VIRTUAL_H + 20) - 10
            xx = (x + dx * yy * 0.08 + self.t * wind * 0.05) % VIRTUAL_W
            pygame.draw.line(surface, (150, 180, 230, 200),
                             (xx, yy), (xx + dx * 0.5, yy + 10), 1)

    def _draw_snow(self, surface):
        wind = self.wind
        for (x, y, sp, ph) in self.parts:
            fall = 60 * sp
            yy = (y + self.t * fall) % (VIRTUAL_H + 10) - 5
            import math
            xx = (x + math.sin(self.t * 1.5 + ph) * 12 + self.t * wind * 0.12) % VIRTUAL_W
            r = 1 + sp
            pygame.draw.circle(surface, (240, 248, 255), (int(xx), int(yy)), int(r))

    def _draw_fog(self, surface):
        veil = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        for (x, y, w, sp) in self.fog:
            xx = (x + self.t * (sp + self.wind * 0.03)) % (VIRTUAL_W + w) - w / 2
            band = pygame.Surface((int(w), 60), pygame.SRCALPHA)
            band.fill((210, 214, 224, 46))
            veil.blit(band, (int(xx), int(y)))
        surface.blit(veil, (0, 0))
