"""Kamera: folgt einem Ziel weich und bleibt in den Levelgrenzen."""
from __future__ import annotations

import pygame

from ..settings import VIRTUAL_W, VIRTUAL_H


class Camera:
    def __init__(self, level_w: int, level_h: int):
        self.level_w = level_w
        self.level_h = level_h
        self.x = 0.0
        self.y = 0.0

    def update(self, target_rect: pygame.Rect, dt: float, snap: bool = False) -> None:
        # Zielposition: Spieler leicht links der Mitte (mehr Vorausblick nach rechts)
        goal_x = target_rect.centerx - VIRTUAL_W * 0.42
        goal_y = target_rect.centery - VIRTUAL_H * 0.55
        if snap:
            self.x, self.y = goal_x, goal_y
        else:
            # exponentielle Glättung
            k = min(1.0, 8.0 * dt)
            self.x += (goal_x - self.x) * k
            self.y += (goal_y - self.y) * k
        self._clamp()

    def _clamp(self) -> None:
        self.x = max(0.0, min(self.x, self.level_w - VIRTUAL_W))
        self.y = max(0.0, min(self.y, self.level_h - VIRTUAL_H))
        if self.level_w < VIRTUAL_W:
            self.x = 0.0
        if self.level_h < VIRTUAL_H:
            self.y = self.level_h - VIRTUAL_H

    @property
    def offset(self) -> tuple[int, int]:
        return (int(self.x), int(self.y))

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        return rect.move(-int(self.x), -int(self.y))
