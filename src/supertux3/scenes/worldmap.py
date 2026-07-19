"""Welt-Karte: Level als Knoten auf einem scrollenden Pfad wählen."""
from __future__ import annotations

import json
import math

import pygame

from ..engine.scene import Scene
from ..engine import controls
from ..settings import VIRTUAL_W, VIRTUAL_H, WHITE, UI_SHADOW, LEVEL_DIR, LEVEL_FILES

# Theme -> (Knotenfarbe, Himmel oben, Himmel unten, Hügelfarbe)
THEME_LOOK = {
    "grass":  ((110, 200, 96), (120, 180, 250), (185, 220, 255), (96, 190, 96)),
    "sunset": ((250, 170, 80), (250, 150, 90), (255, 205, 150), (196, 150, 90)),
    "night":  ((120, 140, 220), (30, 36, 78), (70, 84, 150), (54, 70, 110)),
    "ice":    ((160, 220, 245), (150, 200, 240), (215, 240, 255), (170, 210, 235)),
    "cave":   ((160, 130, 210), (36, 30, 54), (80, 60, 110), (60, 50, 84)),
}
NODE_R = 26
SPACING = 190
MARGIN = 170


class WorldMapScene(Scene):
    def __init__(self, game, selected: int | None = None):
        super().__init__(game)
        self._start_sel = selected

    def on_enter(self):
        self.big = pygame.font.Font(None, 56)
        self.font = pygame.font.Font(None, 32)
        self.small = pygame.font.Font(None, 24)
        self.names, self.themes = [], []
        for f in LEVEL_FILES:
            try:
                d = json.load(open(LEVEL_DIR / f, encoding="utf-8"))
                self.names.append(d.get("name", f))
                self.themes.append(d.get("theme", "grass"))
            except OSError:
                self.names.append(f)
                self.themes.append("grass")
        n = len(LEVEL_FILES)
        self.map_w = MARGIN * 2 + (n - 1) * SPACING
        self.mid_y = VIRTUAL_H * 0.52
        self.nodes = []
        for i in range(n):
            x = MARGIN + i * SPACING
            y = self.mid_y + math.sin(i * 0.85) * 70
            self.nodes.append((x, y))
        self.star_gold = pygame.transform.smoothscale(self.game.assets.star, (16, 16))
        grey = self.game.assets.star.copy()
        grey.fill((90, 96, 110, 255), special_flags=pygame.BLEND_RGBA_MULT)
        self.star_grey = pygame.transform.smoothscale(grey, (16, 16))
        self.pengu = self.game.assets.player["idle"][0]
        self.sel = self._start_sel if self._start_sel is not None \
            else min(getattr(self.game, "level_index", 0), n - 1)
        self.sel = min(self.sel, self.game.unlocked)
        self.cam_x = self._target_cam()
        self.t = 0.0
        self.game.audio.play_music("title.ogg")

    def _target_cam(self):
        return max(0.0, min(self.nodes[self.sel][0] - VIRTUAL_W / 2,
                            self.map_w - VIRTUAL_W))

    # --- Events ------------------------------------------------------
    def handle_event(self, event):
        act = controls.nav(event)
        if act == "right":
            self.sel = min(self.game.unlocked, self.sel + 1)
        elif act == "left":
            self.sel = max(0, self.sel - 1)
        elif act == "confirm":
            from .play import PlayScene
            self.game.lives = 3
            self.game.scenes.switch(PlayScene(self.game, self.sel))
        elif act == "back":
            from .menu import MenuScene
            self.game.scenes.switch(MenuScene(self.game))
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            from .editor import EditorScene
            self.game.scenes.switch(EditorScene(self.game))
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_o:
            from .options import OptionsScene
            self.game.scenes.switch(OptionsScene(self.game))

    def update(self, dt):
        self.t += dt
        self.cam_x += (self._target_cam() - self.cam_x) * min(1.0, 8 * dt)

    # --- Zeichnen ----------------------------------------------------
    def draw(self, surface):
        ox = int(self.cam_x)
        self._draw_bg(surface, ox)
        # Pfad
        for i in range(len(self.nodes) - 1):
            x1, y1 = self.nodes[i]
            x2, y2 = self.nodes[i + 1]
            col = (250, 240, 200) if i < self.game.unlocked else (90, 96, 110)
            pygame.draw.line(surface, (40, 44, 60), (x1 - ox, y1 + 2), (x2 - ox, y2 + 2), 8)
            pygame.draw.line(surface, col, (x1 - ox, y1), (x2 - ox, y2), 5)
        # Knoten
        for i, (x, y) in enumerate(self.nodes):
            sx = x - ox
            if sx < -60 or sx > VIRTUAL_W + 60:
                continue
            locked = i > self.game.unlocked
            base = THEME_LOOK.get(self.themes[i], THEME_LOOK["grass"])[0]
            col = (70, 78, 96) if locked else base
            pygame.draw.circle(surface, (30, 34, 48), (int(sx), int(y)), NODE_R + 3)
            pygame.draw.circle(surface, col, (int(sx), int(y)), NODE_R)
            pygame.draw.circle(surface, WHITE, (int(sx), int(y)), NODE_R, 2)
            num = self.font.render(str(i + 1), True, (20, 24, 36) if not locked else (150, 160, 175))
            surface.blit(num, num.get_rect(center=(sx, y)))
            if not locked:
                got = self.game.best_stars(i)
                for si in range(3):
                    icon = self.star_gold if si < got else self.star_grey
                    surface.blit(icon, (sx - 24 + si * 16, y + NODE_R - 2))
        # Avatar
        ax, ay = self.nodes[self.sel]
        hop = abs(math.sin(self.t * 6)) * 10
        surface.blit(self.pengu, (int(ax - ox - self.pengu.get_width() / 2),
                                  int(ay - NODE_R - self.pengu.get_height() + 4 - hop)))
        self._hud(surface)

    def _draw_bg(self, surface, ox):
        top = THEME_LOOK.get(self.themes[self.sel], THEME_LOOK["grass"])[1]
        bot = THEME_LOOK.get(self.themes[self.sel], THEME_LOOK["grass"])[2]
        for y in range(VIRTUAL_H):
            f = y / (VIRTUAL_H - 1)
            col = tuple(int(top[i] + (bot[i] - top[i]) * f) for i in range(3))
            pygame.draw.line(surface, col, (0, y), (VIRTUAL_W, y))
        # sanfte Hügel als Band unter dem Pfad
        hill = THEME_LOOK.get(self.themes[self.sel], THEME_LOOK["grass"])[3]
        pts = [(0, VIRTUAL_H)]
        for sx in range(0, VIRTUAL_W + 20, 20):
            wx = sx + ox
            hy = self.mid_y + 60 + math.sin(wx * 0.004) * 40
            pts.append((sx, hy))
        pts.append((VIRTUAL_W, VIRTUAL_H))
        pygame.draw.polygon(surface, hill, pts)

    def _hud(self, surface):
        veil = pygame.Surface((VIRTUAL_W, 54), pygame.SRCALPHA)
        veil.fill((10, 14, 28, 150))
        surface.blit(veil, (0, 0))
        name = f"{self.sel + 1}. {self.names[self.sel]}"
        self._text(surface, name, self.big, (14, 4), (255, 240, 120))
        total = sum(self.game.best_stars(i) for i in range(len(LEVEL_FILES)))
        self._text(surface, f"Sterne gesamt: {total}/{len(LEVEL_FILES) * 3}",
                   self.small, (VIRTUAL_W - 230, 8), (255, 232, 150))
        bt = self.game.best_time(self.sel)
        if bt > 0:
            m, s = divmod(int(bt), 60)
            self._text(surface, f"Bestzeit {m}:{s:02d}", self.small,
                       (VIRTUAL_W - 230, 30), (200, 220, 245))
        self._center(surface, "Links/Rechts wählen · ENTER spielen · E Editor · O Optionen · ESC Menü",
                     self.small, (215, 225, 240), VIRTUAL_H - 22)

    def _text(self, surface, text, font, pos, color):
        surface.blit(font.render(text, True, UI_SHADOW), (pos[0] + 2, pos[1] + 2))
        surface.blit(font.render(text, True, color), pos)

    def _center(self, surface, text, font, color, y):
        img = font.render(text, True, color)
        rect = img.get_rect(center=(VIRTUAL_W // 2, y))
        surface.blit(font.render(text, True, UI_SHADOW), rect.move(2, 2))
        surface.blit(img, rect)
