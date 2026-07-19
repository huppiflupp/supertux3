"""Tastenbelegung frei konfigurieren."""
from __future__ import annotations

import pygame

from ..engine.scene import Scene
from ..engine import controls
from ..settings import VIRTUAL_W, VIRTUAL_H, WHITE, UI_SHADOW


class KeybindScene(Scene):
    def __init__(self, game, back_scene=None):
        super().__init__(game)
        self.back_scene = back_scene

    def on_enter(self):
        self.title_font = pygame.font.Font(None, 64)
        self.font = pygame.font.Font(None, 38)
        self.small = pygame.font.Font(None, 26)
        self.sel = 0
        self.capturing = False
        # Aktionen + Sonderpunkte
        self.rows = list(controls.ACTIONS) + ["_reset", "_back"]

    def _leave(self):
        target = self.back_scene
        if target is None:
            from .options import OptionsScene
            target = OptionsScene(self.game)
        self.game.scenes.switch(target)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.capturing:
            if event.key != pygame.K_ESCAPE:
                action = self.rows[self.sel]
                self.game.keys[action] = [event.key]
                self.game.save_progress()
            self.capturing = False
            return
        k = event.key
        if k in (pygame.K_UP, pygame.K_w):
            self.sel = (self.sel - 1) % len(self.rows)
        elif k in (pygame.K_DOWN, pygame.K_s):
            self.sel = (self.sel + 1) % len(self.rows)
        elif k in (pygame.K_RETURN, pygame.K_SPACE):
            row = self.rows[self.sel]
            if row == "_back":
                self._leave()
            elif row == "_reset":
                self.game.keys = {a: list(v) for a, v in controls.DEFAULT_KEYS.items()}
                self.game.save_progress()
            else:
                self.capturing = True
        elif k == pygame.K_ESCAPE:
            self._leave()

    def draw(self, surface):
        surface.fill((30, 44, 72))
        for i in range(0, VIRTUAL_H, 4):
            c = 28 + int(24 * i / VIRTUAL_H)
            pygame.draw.line(surface, (c - 8, c + 8, c + 34), (0, i), (VIRTUAL_W, i))
        self._center(surface, "Tastenbelegung", self.title_font, (255, 240, 120), 60)

        y0 = 140
        for i, row in enumerate(self.rows):
            y = y0 + i * 54
            selected = i == self.sel
            col = (255, 236, 130) if selected else WHITE
            prefix = "> " if selected else "  "
            if row == "_reset":
                label, val = "Standard wiederherstellen", ""
            elif row == "_back":
                label, val = "Zurück", ""
            else:
                label = controls.ACTION_LABEL[row]
                if selected and self.capturing:
                    val = "… Taste drücken (ESC bricht ab)"
                else:
                    val = " / ".join(controls.key_label(k) for k in self.game.keys[row])
            self._text(surface, prefix + label, self.font, (VIRTUAL_W // 2 - 300, y), col)
            if val:
                self._text(surface, val, self.font, (VIRTUAL_W // 2 + 20, y), col)

        self._center(surface, "Hoch/Runter wählen · ENTER belegen · ESC zurück",
                     self.small, (210, 220, 240), VIRTUAL_H - 26)

    def _text(self, surface, text, font, pos, color):
        surface.blit(font.render(text, True, UI_SHADOW), (pos[0] + 2, pos[1] + 2))
        surface.blit(font.render(text, True, color), pos)

    def _center(self, surface, text, font, color, y):
        img = font.render(text, True, color)
        rect = img.get_rect(center=(VIRTUAL_W // 2, y))
        surface.blit(font.render(text, True, UI_SHADOW), rect.move(2, 2))
        surface.blit(img, rect)
