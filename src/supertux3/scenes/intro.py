"""Kurze animierte Titel-Intro (überspringbar)."""
from __future__ import annotations

import pygame

from ..engine.scene import Scene
from ..engine.animation import Animation
from ..settings import VIRTUAL_W, VIRTUAL_H, GAME_TITLE, SKY_TOP, SKY_BOTTOM, WHITE, UI_SHADOW, TILE


class IntroScene(Scene):
    DURATION = 4.0

    def on_enter(self):
        self.t = 0.0
        self.title_font = pygame.font.Font(None, 150)
        self.font = pygame.font.Font(None, 30)
        self.sky = self._gradient()
        self.walk = Animation(self.game.assets.player["walk"], fps=12)
        self.ground_y = VIRTUAL_H - 70
        self.game.audio.play_music("title.ogg")

    def _gradient(self):
        surf = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        for y in range(VIRTUAL_H):
            f = y / (VIRTUAL_H - 1)
            col = tuple(int(SKY_TOP[i] + (SKY_BOTTOM[i] - SKY_TOP[i]) * f) for i in range(3))
            pygame.draw.line(surf, col, (0, y), (VIRTUAL_W, y))
        return surf

    def handle_event(self, event):
        from ..engine.controls import nav
        if nav(event) or event.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN):
            self._to_menu()

    def _to_menu(self):
        from .menu import MenuScene
        self.game.scenes.switch(MenuScene(self.game))

    def update(self, dt):
        self.t += dt
        self.walk.update(dt)
        if self.t >= self.DURATION:
            self._to_menu()

    def _title_y(self):
        # fällt von oben mit weichem Ausklang + kleinem Nachwippen
        p = min(1.0, self.t / 1.1)
        ease = 1 - (1 - p) ** 3
        import math
        wobble = math.sin(self.t * 8) * max(0.0, 6 * (1 - p)) if p >= 1 else 0
        return int(-120 + ease * (VIRTUAL_H * 0.36 + 120)) + wobble

    def draw(self, surface):
        surface.blit(self.sky, (0, 0))
        # Hügel
        pygame.draw.ellipse(surface, (108, 196, 96),
                            (-100, self.ground_y - 30, VIRTUAL_W + 200, 300))
        pygame.draw.rect(surface, (96, 180, 84), (0, self.ground_y + 20, VIRTUAL_W, 80))

        # laufender Pengu
        speed = (VIRTUAL_W + 120) / self.DURATION
        px = int(-60 + self.t * speed)
        img = self.walk.image
        surface.blit(img, (px, self.ground_y - img.get_height() + 6))

        # Titel
        ty = self._title_y()
        img = self.title_font.render(GAME_TITLE, True, (255, 240, 120))
        rect = img.get_rect(center=(VIRTUAL_W // 2, ty))
        surface.blit(self.title_font.render(GAME_TITLE, True, UI_SHADOW), rect.move(4, 4))
        surface.blit(img, rect)

        if self.t > 1.6 and int(self.t * 2) % 2 == 0:
            s = self.font.render("Taste drücken", True, WHITE)
            surface.blit(s, s.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H - 24)))
