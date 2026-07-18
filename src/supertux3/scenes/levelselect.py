"""Level-Auswahl."""
from __future__ import annotations

import json
import math

import pygame

from ..engine.scene import Scene
from ..settings import VIRTUAL_W, VIRTUAL_H, WHITE, UI_SHADOW, LEVEL_DIR, LEVEL_FILES


class LevelSelectScene(Scene):
    def on_enter(self):
        self.title_font = pygame.font.Font(None, 84)
        self.font = pygame.font.Font(None, 40)
        self.small = pygame.font.Font(None, 28)
        self.names = []
        for f in LEVEL_FILES:
            try:
                with open(LEVEL_DIR / f, "r", encoding="utf-8") as fh:
                    self.names.append(json.load(fh).get("name", f))
            except OSError:
                self.names.append(f)
        self.sel = min(getattr(self.game, "level_index", 0), len(LEVEL_FILES) - 1)
        self.t = 0.0
        self.game.audio.play_music("title.ogg")

    def handle_event(self, event):
        from ..engine.controls import nav
        act = nav(event)
        n = len(LEVEL_FILES)
        cols = 2
        if act == "right":
            self.sel = (self.sel + 1) % n
        elif act == "left":
            self.sel = (self.sel - 1) % n
        elif act == "down":
            self.sel = (self.sel + cols) % n
        elif act == "up":
            self.sel = (self.sel - cols) % n
        elif act == "confirm":
            if self.sel <= self.game.unlocked:
                from .play import PlayScene
                self.game.scenes.switch(PlayScene(self.game, self.sel))
        elif act == "back":
            from .menu import MenuScene
            self.game.scenes.switch(MenuScene(self.game))

    def update(self, dt):
        self.t += dt

    def draw(self, surface):
        surface.fill((40, 62, 96))
        for i in range(0, VIRTUAL_H, 4):
            c = 40 + int(30 * i / VIRTUAL_H)
            pygame.draw.line(surface, (c - 10, c + 10, c + 40), (0, i), (VIRTUAL_W, i))
        self._center(surface, "Level-Auswahl", self.title_font, (255, 240, 120), 54)

        cols = 2
        cw, ch = 400, 60
        gap_x, gap_y = 40, 14
        rows = (len(self.names) + cols - 1) // cols
        total_w = cols * cw + (cols - 1) * gap_x
        x0 = (VIRTUAL_W - total_w) // 2
        y0 = 108
        for i, name in enumerate(self.names):
            r, c = divmod(i, cols)
            x = x0 + c * (cw + gap_x)
            y = y0 + r * (ch + gap_y)
            locked = i > self.game.unlocked
            selected = i == self.sel
            box = pygame.Rect(x, y, cw, ch)
            base = (30, 40, 66) if locked else (58, 92, 150)
            if selected:
                grow = int(3 + 3 * (0.5 + 0.5 * math.sin(self.t * 6)))
                pygame.draw.rect(surface, (255, 230, 120), box.inflate(grow * 2, grow * 2),
                                 border_radius=10)
            pygame.draw.rect(surface, base, box, border_radius=8)
            pygame.draw.rect(surface, (20, 26, 44), box, width=2, border_radius=8)
            num = self.font.render(f"{i + 1}", True,
                                   (255, 240, 160) if not locked else (120, 130, 150))
            surface.blit(num, (x + 14, y + ch // 2 - num.get_height() // 2))
            label = name if not locked else "gesperrt"
            col = WHITE if not locked else (130, 140, 160)
            img = self.font.render(label, True, col)
            surface.blit(img, (x + 58, y + 8))
            if not locked:
                bs = self.small.render(f"Münzen: {self.game.best_coins(i)}",
                                       True, (255, 232, 150))
                surface.blit(bs, (x + 58, y + ch - 26))

        self._center(surface, "Pfeile wählen · ENTER spielen · ESC zurück",
                     self.small, (215, 225, 240), VIRTUAL_H - 22)

    def _center(self, surface, text, font, color, y):
        img = font.render(text, True, color)
        rect = img.get_rect(center=(VIRTUAL_W // 2, y))
        surface.blit(font.render(text, True, UI_SHADOW), rect.move(2, 2))
        surface.blit(img, rect)
