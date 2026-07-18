"""Level-Auswahl."""
from __future__ import annotations

import json
import math

import pygame

from ..engine.scene import Scene
from ..settings import VIRTUAL_W, VIRTUAL_H, WHITE, UI_SHADOW, LEVEL_DIR, LEVEL_FILES


class LevelSelectScene(Scene):
    COLS = 3

    def on_enter(self):
        self.title_font = pygame.font.Font(None, 76)
        self.font = pygame.font.Font(None, 30)
        self.small = pygame.font.Font(None, 22)
        self.names = []
        for f in LEVEL_FILES:
            try:
                with open(LEVEL_DIR / f, "r", encoding="utf-8") as fh:
                    self.names.append(json.load(fh).get("name", f))
            except OSError:
                self.names.append(f)
        self.sel = min(getattr(self.game, "level_index", 0), len(LEVEL_FILES) - 1)
        self.t = 0.0
        star = self.game.assets.star
        self.star_gold = pygame.transform.smoothscale(star, (18, 18))
        grey = star.copy()
        grey.fill((90, 96, 110, 255), special_flags=pygame.BLEND_RGBA_MULT)
        self.star_grey = pygame.transform.smoothscale(grey, (18, 18))
        self.game.audio.play_music("title.ogg")

    def handle_event(self, event):
        from ..engine.controls import nav
        act = nav(event)
        n = len(LEVEL_FILES)
        cols = self.COLS
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
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            from .editor import EditorScene
            self.game.scenes.switch(EditorScene(self.game))

    def update(self, dt):
        self.t += dt

    def draw(self, surface):
        surface.fill((40, 62, 96))
        for i in range(0, VIRTUAL_H, 4):
            c = 40 + int(30 * i / VIRTUAL_H)
            pygame.draw.line(surface, (c - 10, c + 10, c + 40), (0, i), (VIRTUAL_W, i))
        self._center(surface, "Level-Auswahl", self.title_font, (255, 240, 120), 44)

        cols = self.COLS
        cw, ch = 300, 66
        gap_x, gap_y = 12, 10
        total_w = cols * cw + (cols - 1) * gap_x
        x0 = (VIRTUAL_W - total_w) // 2
        y0 = 88
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
                                 border_radius=8)
            pygame.draw.rect(surface, base, box, border_radius=8)
            pygame.draw.rect(surface, (20, 26, 44), box, width=2, border_radius=8)
            num = self.small.render(f"{i + 1}", True,
                                    (255, 240, 160) if not locked else (120, 130, 150))
            surface.blit(num, (x + 8, y + 6))
            label = name if not locked else "gesperrt"
            col = WHITE if not locked else (130, 140, 160)
            img = self.font.render(label, True, col)
            surface.blit(img, (x + 30, y + 6))
            if not locked:
                bt = self.game.best_time(i)
                tstr = ""
                if bt > 0:
                    m, s = divmod(int(bt), 60)
                    tstr = f"  ·  {m}:{s:02d}"
                bs = self.small.render(f"Münzen {self.game.best_coins(i)}{tstr}",
                                       True, (255, 232, 150))
                surface.blit(bs, (x + 30, y + ch - 24))
                got = self.game.best_stars(i)
                for si in range(3):
                    icon = self.star_gold if si < got else self.star_grey
                    surface.blit(icon, (x + cw - 66 + si * 20, y + 10))

        self._center(surface, "Pfeile wählen · ENTER spielen · E Editor · ESC zurück",
                     self.small, (215, 225, 240), VIRTUAL_H - 18)

    def _center(self, surface, text, font, color, y):
        img = font.render(text, True, color)
        rect = img.get_rect(center=(VIRTUAL_W // 2, y))
        surface.blit(font.render(text, True, UI_SHADOW), rect.move(2, 2))
        surface.blit(img, rect)
