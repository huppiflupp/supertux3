"""Welt-Karte im Super-Mario-Stil.

Die 15 Level liegen als Knoten auf einem gewundenen Pfad, der sich über eine
breite, seitlich scrollende Karte zieht. Je nach Level-``theme`` (grass,
sunset, night, ice, cave) verwandelt sich die prozedural gezeichnete, sanft
animierte Kulisse. Am fernen Horizont locken kleine Teaser auf kommende Welten
(Rakete/Weltraum, Pyramide/Ägypten, Stadt-Skyline/Großstadt). Ein Pengu-Avatar
hüpft auf dem gewählten Knoten.

Alles wird zur Laufzeit mit pygame gezeichnet – keine externen Assets außer den
ohnehin vorhandenen Sprites (Pengu, Stern).
"""
from __future__ import annotations

import json
import math
import random

import pygame

from ..engine.scene import Scene
from ..engine import controls
from ..settings import VIRTUAL_W, VIRTUAL_H, WHITE, UI_SHADOW, LEVEL_DIR, LEVEL_FILES

# Theme -> (Knotenfarbe, Himmel oben, Himmel unten, Grundfarbe/Hügel)
THEME_LOOK = {
    "grass":  ((110, 200, 96), (120, 180, 250), (198, 228, 255), (96, 190, 96)),
    "sunset": ((250, 170, 80), (74, 62, 120), (255, 178, 120), (150, 96, 120)),
    "night":  ((120, 140, 220), (16, 20, 52), (58, 68, 128), (40, 52, 92)),
    "ice":    ((160, 220, 245), (140, 196, 240), (224, 244, 255), (176, 214, 236)),
    "cave":   ((180, 130, 220), (26, 20, 42), (66, 48, 92), (46, 36, 66)),
    "egypt":  ((234, 194, 120), (250, 200, 120), (255, 236, 186), (214, 178, 116)),
    "space":  ((170, 140, 230), (10, 10, 34), (40, 28, 66), (60, 60, 92)),
}
NODE_R = 26
SPACING = 200
MARGIN = 180
HORIZON = int(VIRTUAL_H * 0.62)   # y der Landschafts-Silhouette


class WorldMapScene(Scene):
    def __init__(self, game, selected: int | None = None):
        super().__init__(game)
        self._start_sel = selected

    # --- Aufbau ------------------------------------------------------
    def on_enter(self):
        self.big = pygame.font.Font(None, 54)
        self.font = pygame.font.Font(None, 32)
        self.small = pygame.font.Font(None, 24)
        self.tiny = pygame.font.Font(None, 20)

        # Namen + Themes aus den Level-JSONs lesen
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
        self.mid_y = VIRTUAL_H * 0.48
        # Gewundener Pfad: die Knoten wiegen sich in weichen Wellen
        self.nodes = []
        for i in range(n):
            x = MARGIN + i * SPACING
            y = self.mid_y + math.sin(i * 0.8) * 62 + math.sin(i * 1.9) * 16
            self.nodes.append((x, y))

        # Stern-Icons (gold + ausgegraut) vorbereiten
        self.star_gold = pygame.transform.smoothscale(self.game.assets.star, (18, 18))
        grey = self.game.assets.star.copy()
        grey.fill((86, 92, 108, 255), special_flags=pygame.BLEND_RGBA_MULT)
        self.star_grey = pygame.transform.smoothscale(grey, (18, 18))
        self.pengu = self.game.assets.player["idle"][0]

        # Himmel-Verläufe je Theme einmalig vorrendern (spart 540 Linien/Frame)
        self._sky_cache: dict[str, pygame.Surface] = {}
        for th, look in THEME_LOOK.items():
            self._sky_cache[th] = self._make_sky(look[1], look[2])
        # Glow-Sprites (Sonne/Mond/Kristalle) gecacht
        self._glow_cache: dict[tuple, pygame.Surface] = {}

        # Deterministische Deko-Positionen (Sterne, Schnee, Wolken, Kristalle)
        self._build_decor()

        self.sel = self._start_sel if self._start_sel is not None \
            else min(getattr(self.game, "level_index", 0), n - 1)
        self.sel = min(self.sel, self.game.unlocked)
        self.cam_x = self._target_cam()
        self.t = 0.0
        self.game.audio.play_music("title.ogg")

    def _build_decor(self):
        rng = random.Random(0x570153)
        # Funkelnde Sterne (bildschirmfest, weil unendlich fern)
        self.stars = [(rng.uniform(0, VIRTUAL_W), rng.uniform(0, self.mid_y + 30),
                       rng.uniform(1.4, 3.0), rng.uniform(0, 6.28), rng.uniform(1.5, 3.4))
                      for _ in range(90)]
        # Schneeflocken (bildschirmfest, fallen + driften, wrappen)
        self.snow = [(rng.uniform(0, VIRTUAL_W), rng.uniform(0, VIRTUAL_H),
                      rng.uniform(28, 70), rng.uniform(6, 18), rng.uniform(0, 6.28),
                      rng.uniform(1.6, 3.2))
                     for _ in range(70)]
        # Parallax-Wolken (Weltkoordinate, Höhe, Größe, Eigen-Drift)
        self.clouds = [(rng.uniform(-200, self.map_w + 200), rng.uniform(30, self.mid_y - 50),
                        rng.uniform(0.7, 1.6), rng.uniform(3, 9))
                       for _ in range(14)]
        # Leuchtkristalle für Höhlen-Regionen (Weltkoordinate am Boden)
        self.crystals = [(rng.uniform(0, self.map_w),
                          HORIZON + rng.uniform(10, 120),
                          rng.uniform(14, 34), rng.uniform(0, 6.28),
                          rng.choice([(150, 230, 255), (200, 150, 255), (150, 255, 200)]))
                         for _ in range(26)]

    def _make_sky(self, top, bot):
        surf = pygame.Surface((VIRTUAL_W, VIRTUAL_H)).convert()
        for y in range(VIRTUAL_H):
            f = y / (VIRTUAL_H - 1)
            col = tuple(int(top[i] + (bot[i] - top[i]) * f) for i in range(3))
            pygame.draw.line(surf, col, (0, y), (VIRTUAL_W, y))
        return surf

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
        # Kamera weich zum gewählten Knoten ziehen
        self.cam_x += (self._target_cam() - self.cam_x) * min(1.0, 8 * dt)

    # =================================================================
    #  Zeichnen
    # =================================================================
    def draw(self, surface):
        ox = int(self.cam_x)
        theme = self.themes[self.sel]
        surface.blit(self._sky_cache.get(theme, self._sky_cache["grass"]), (0, 0))
        self._draw_celestial(surface, theme)     # Sonne/Mond/Sterne
        self._draw_teasers(surface)              # ferne kommende Welten
        self._draw_clouds(surface, ox, theme)    # Parallax-Wolken
        self._draw_scenery(surface, ox, theme)   # Region-Kulisse (Hügel/Berge/…)
        self._draw_weather(surface, theme)       # Schneefall
        self._draw_path(surface, ox)
        self._draw_nodes(surface, ox)
        self._draw_avatar(surface, ox)
        self._hud(surface)

    # --- Himmelskörper ----------------------------------------------
    def _draw_celestial(self, surface, theme):
        if theme == "night":
            # funkelnde Sterne
            for x, y, size, phase, speed in self.stars:
                tw = 0.5 + 0.5 * math.sin(self.t * speed + phase)
                b = int(150 + 105 * tw)
                r = max(1, int(size * (0.6 + 0.4 * tw)))
                pygame.draw.circle(surface, (b, b, min(255, b + 25)), (int(x), int(y)), r)
            # Mond mit Kratern + Glow
            mx, my = VIRTUAL_W - 150, 110
            surface.blit(self._glow(90, (230, 235, 255, 60)), (mx - 90, my - 90))
            pygame.draw.circle(surface, (238, 240, 250), (mx, my), 44)
            pygame.draw.circle(surface, (206, 212, 232), (mx, my), 44, 3)
            for dx, dy, r in ((-14, -8, 8), (12, 6, 6), (-4, 16, 5), (18, -14, 4)):
                pygame.draw.circle(surface, (208, 214, 234), (mx + dx, my + dy), r)
        elif theme == "sunset":
            sx, sy = int(VIRTUAL_W * 0.30), HORIZON - 40
            surface.blit(self._glow(190, (255, 190, 120, 90)), (sx - 190, sy - 190))
            pygame.draw.circle(surface, (255, 226, 150), (sx, sy), 66)
            pygame.draw.circle(surface, (255, 244, 200), (sx, sy), 52)
        elif theme in ("grass", "ice"):
            sx, sy = VIRTUAL_W - 150, 96
            glow = (255, 245, 190, 80) if theme == "grass" else (220, 240, 255, 70)
            surface.blit(self._glow(120, glow), (sx - 120, sy - 120))
            pygame.draw.circle(surface, (255, 246, 200), (sx, sy), 40)

    # --- Ferne Teaser (kommende Welten am Horizont) ------------------
    def _draw_teasers(self, surface):
        # sanftes Schweben, damit die Silhouetten leicht "leben"
        bob = math.sin(self.t * 0.8) * 2
        self._teaser_rocket(surface, int(VIRTUAL_W * 0.16), HORIZON - 30 + bob)
        self._teaser_pyramids(surface, int(VIRTUAL_W * 0.52), HORIZON - 6)
        self._teaser_city(surface, int(VIRTUAL_W * 0.83), HORIZON - 4)

    def _teaser_rocket(self, surface, x, base):
        col = (120, 128, 150)
        top = base - 46
        # Rumpf
        pygame.draw.polygon(surface, (150, 156, 176),
                            [(x, top), (x - 8, top + 14), (x - 8, base - 8),
                             (x + 8, base - 8), (x + 8, top + 14)])
        pygame.draw.circle(surface, (110, 170, 210), (x, top + 20), 4)  # Fenster
        # Finnen
        pygame.draw.polygon(surface, col, [(x - 8, base - 16), (x - 16, base - 4), (x - 8, base - 4)])
        pygame.draw.polygon(surface, col, [(x + 8, base - 16), (x + 16, base - 4), (x + 8, base - 4)])
        # flackernde Flamme
        fl = 8 + int(4 * abs(math.sin(self.t * 9)))
        pygame.draw.polygon(surface, (255, 190, 90),
                            [(x - 5, base - 6), (x + 5, base - 6), (x, base - 6 + fl)])

    def _teaser_pyramids(self, surface, x, base):
        sand = (150, 122, 96)
        pygame.draw.polygon(surface, sand, [(x - 46, base), (x, base - 54), (x + 46, base)])
        pygame.draw.polygon(surface, (168, 138, 108),
                            [(x, base - 54), (x + 46, base), (x + 14, base)])
        pygame.draw.polygon(surface, sand, [(x + 26, base), (x + 62, base - 34), (x + 98, base)])
        # kleine Sphinx
        sx = x - 74
        pygame.draw.rect(surface, (158, 130, 100), (sx, base - 12, 26, 12))
        pygame.draw.circle(surface, (158, 130, 100), (sx, base - 14), 7)

    def _teaser_city(self, surface, x, base):
        cols = [(96, 104, 130), (110, 118, 146), (84, 92, 118)]
        for i, (dx, w, h) in enumerate(((-46, 20, 40), (-22, 24, 62),
                                        (6, 20, 48), (30, 26, 70))):
            pygame.draw.rect(surface, cols[i % 3], (x + dx, base - h, w, h))
            # Fensterreihen
            for wy in range(base - h + 6, base - 6, 12):
                for wx in range(x + dx + 4, x + dx + w - 4, 8):
                    pygame.draw.rect(surface, (190, 210, 150), (wx, wy, 3, 4))
        # Baukran
        cx = x + 60
        pygame.draw.line(surface, (200, 170, 70), (cx, base), (cx, base - 78), 3)
        pygame.draw.line(surface, (200, 170, 70), (cx - 24, base - 70), (cx + 40, base - 70), 3)
        pygame.draw.line(surface, (150, 150, 160), (cx + 30, base - 70), (cx + 30, base - 52), 2)

    # --- Wolken ------------------------------------------------------
    def _draw_clouds(self, surface, ox, theme):
        if theme == "cave":
            return
        tint = (245, 250, 255) if theme != "night" else (120, 128, 168)
        if theme == "sunset":
            tint = (255, 200, 170)
        span = VIRTUAL_W + 400
        for wx, y, sc, drift in self.clouds:
            # Parallax + langsame Eigenbewegung, dann über den Bildschirm wrappen
            sx = (wx - ox * 0.35 + self.t * drift) % span - 200
            self._cloud(surface, sx, y, sc, tint)

    def _cloud(self, surface, x, y, sc, col):
        x, y = int(x), int(y)
        for dx, dy, r in ((0, 0, 20), (18, 4, 16), (-18, 4, 15), (34, 8, 12), (-32, 8, 11)):
            pygame.draw.circle(surface, col, (x + int(dx * sc), y + int(dy * sc)),
                               max(4, int(r * sc)))
        pygame.draw.rect(surface, col, (x - int(32 * sc), y + int(6 * sc),
                                        int(64 * sc), int(10 * sc)))

    # --- Region-Kulisse ---------------------------------------------
    def _draw_scenery(self, surface, ox, theme):
        look = THEME_LOOK.get(theme, THEME_LOOK["grass"])
        if theme == "sunset":
            self._mountains(surface, ox, (108, 72, 104), 0.35, 150)
            self._mountains(surface, ox, (74, 52, 84), 0.6, 90)
            self._ground(surface, ox, look[3])
        elif theme == "ice":
            self._mountains(surface, ox, (196, 222, 240), 0.35, 150)
            self._mountains(surface, ox, (168, 204, 230), 0.6, 90)
            self._ground(surface, ox, look[3], snowcap=True)
        elif theme == "cave":
            self._cave(surface, ox, look[3])
        elif theme == "night":
            self._mountains(surface, ox, (30, 40, 74), 0.35, 140)
            self._hills(surface, ox, look[3])
        else:  # grass
            self._hills(surface, ox, (150, 210, 140), 0.4, amp=44, lift=30)
            self._hills(surface, ox, look[3])

    def _hills(self, surface, ox, col, par=1.0, amp=40, lift=0):
        """Weiche, wogende Hügel als gefülltes Band."""
        pts = [(-4, VIRTUAL_H)]
        for sx in range(-4, VIRTUAL_W + 24, 16):
            wx = sx + ox * par
            hy = HORIZON + lift + math.sin(wx * 0.006) * amp + math.sin(wx * 0.017) * (amp * 0.4)
            pts.append((sx, hy))
        pts.append((VIRTUAL_W + 4, VIRTUAL_H))
        pygame.draw.polygon(surface, col, pts)

    def _mountains(self, surface, ox, col, par, height):
        """Gezackte Berg-Silhouette."""
        pts = [(-4, VIRTUAL_H)]
        step = 90
        sx = -step
        k = 0
        while sx < VIRTUAL_W + step:
            wx = sx + ox * par
            peak = HORIZON - height * (0.6 + 0.4 * abs(math.sin(wx * 0.004 + k)))
            pts.append((sx, HORIZON))
            pts.append((sx + step // 2, peak))
            sx += step
            k += 1
        pts.append((VIRTUAL_W + 4, HORIZON))
        pts.append((VIRTUAL_W + 4, VIRTUAL_H))
        pygame.draw.polygon(surface, col, pts)

    def _ground(self, surface, ox, col, snowcap=False):
        top = HORIZON + 40
        pygame.draw.rect(surface, col, (0, top, VIRTUAL_W, VIRTUAL_H - top))
        if snowcap:
            cap = tuple(min(255, c + 30) for c in col)
            pygame.draw.rect(surface, cap, (0, top, VIRTUAL_W, 8))

    def _cave(self, surface, ox, col):
        # Bodenfläche der Höhle
        pygame.draw.rect(surface, col, (0, HORIZON, VIRTUAL_W, VIRTUAL_H - HORIZON))
        # Stalaktiten von oben
        dark = tuple(max(0, c - 12) for c in col)
        for bx in range(-40, VIRTUAL_W + 40, 70):
            sx = bx - int(ox * 0.5) % 70
            h = 40 + (bx // 70 % 3) * 18
            pygame.draw.polygon(surface, dark, [(sx, 0), (sx + 34, 0), (sx + 17, h)])
        # leuchtende Kristalle am Boden (pulsierend)
        for wx, wy, size, phase, ccol in self.crystals:
            sx = wx - ox * 0.6
            if sx < -40 or sx > VIRTUAL_W + 40:
                continue
            pulse = 0.6 + 0.4 * math.sin(self.t * 2.2 + phase)
            gr = int(size * 2.2 * pulse)
            surface.blit(self._glow(gr, (*ccol, int(90 * pulse))),
                         (int(sx - gr), int(wy - gr)))
            pygame.draw.polygon(surface, ccol,
                                [(sx, wy - size), (sx - size * 0.4, wy),
                                 (sx, wy + size * 0.3), (sx + size * 0.4, wy)])
            bright = tuple(min(255, c + 40) for c in ccol)
            pygame.draw.polygon(surface, bright,
                                [(sx, wy - size), (sx - size * 0.4, wy), (sx, wy)])

    # --- Wetter (Schnee) --------------------------------------------
    def _draw_weather(self, surface, theme):
        if theme != "ice":
            return
        for x0, y0, fall, drift, phase, size in self.snow:
            y = (y0 + self.t * fall) % (VIRTUAL_H + 10)
            x = (x0 + math.sin(self.t * 0.9 + phase) * drift) % VIRTUAL_W
            pygame.draw.circle(surface, (245, 250, 255), (int(x), int(y)), int(size))

    # --- Pfad + Knoten ----------------------------------------------
    def _draw_path(self, surface, ox):
        for i in range(len(self.nodes) - 1):
            x1, y1 = self.nodes[i]
            x2, y2 = self.nodes[i + 1]
            done = i < self.game.unlocked
            # Schatten
            pygame.draw.line(surface, (30, 34, 50), (x1 - ox, y1 + 4), (x2 - ox, y2 + 4), 12)
            base = (250, 224, 150) if done else (96, 102, 120)
            pygame.draw.line(surface, base, (x1 - ox, y1), (x2 - ox, y2), 9)
            # gestrichelte Mittellinie für freigeschaltete Abschnitte
            if done:
                dist = math.hypot(x2 - x1, y2 - y1)
                steps = max(1, int(dist / 16))
                for s in range(steps):
                    if s % 2:
                        continue
                    f0, f1 = s / steps, (s + 1) / steps
                    p0 = (x1 + (x2 - x1) * f0 - ox, y1 + (y2 - y1) * f0)
                    p1 = (x1 + (x2 - x1) * f1 - ox, y1 + (y2 - y1) * f1)
                    pygame.draw.line(surface, (255, 246, 210), p0, p1, 3)

    def _draw_nodes(self, surface, ox):
        for i, (x, y) in enumerate(self.nodes):
            sx = x - ox
            if sx < -70 or sx > VIRTUAL_W + 70:
                continue
            locked = i > self.game.unlocked
            selected = i == self.sel
            base = THEME_LOOK.get(self.themes[i], THEME_LOOK["grass"])[0]
            col = (74, 80, 100) if locked else base
            # Auswahl-Ring pulsiert
            if selected:
                ring = NODE_R + 8 + int(3 * math.sin(self.t * 5))
                pygame.draw.circle(surface, (255, 238, 140), (int(sx), int(y)), ring, 3)
            pygame.draw.circle(surface, (26, 30, 44), (int(sx), int(y)), NODE_R + 3)
            pygame.draw.circle(surface, col, (int(sx), int(y)), NODE_R)
            # Glanzlicht oben (glossy Look)
            hi = tuple(min(255, c + 55) for c in col)
            pygame.draw.circle(surface, hi, (int(sx), int(y - NODE_R * 0.35)),
                               int(NODE_R * 0.55))
            pygame.draw.circle(surface, WHITE, (int(sx), int(y)), NODE_R, 2)
            num = self.font.render(str(i + 1), True,
                                   (150, 160, 175) if locked else (24, 28, 40))
            surface.blit(num, num.get_rect(center=(sx, y)))
            if locked:
                continue
            # Sterne unter dem Knoten
            got = self.game.best_stars(i)
            for si in range(3):
                icon = self.star_gold if si < got else self.star_grey
                surface.blit(icon, (sx - 27 + si * 18, y + NODE_R + 2))

    def _draw_avatar(self, surface, ox):
        ax, ay = self.nodes[self.sel]
        hop = abs(math.sin(self.t * 6)) * 12
        surface.blit(self.pengu, (int(ax - ox - self.pengu.get_width() / 2),
                                  int(ay - NODE_R - self.pengu.get_height() + 4 - hop)))

    # --- Glow-Helfer -------------------------------------------------
    def _glow(self, radius, rgba):
        radius = max(2, int(radius))
        key = (radius, rgba)
        surf = self._glow_cache.get(key)
        if surf is not None:
            return surf
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        r, g, b, a = rgba
        for rr in range(radius, 0, -2):
            aa = int(a * (rr / radius) ** 2)
            pygame.draw.circle(surf, (r, g, b, aa), (radius, radius), radius - rr + 1)
        self._glow_cache[key] = surf
        return surf

    # --- HUD ---------------------------------------------------------
    def _hud(self, surface):
        veil = pygame.Surface((VIRTUAL_W, 56), pygame.SRCALPHA)
        veil.fill((10, 14, 28, 160))
        surface.blit(veil, (0, 0))
        name = f"{self.sel + 1}. {self.names[self.sel]}"
        self._text(surface, name, self.big, (16, 6), (255, 240, 120))
        total = sum(self.game.best_stars(i) for i in range(len(LEVEL_FILES)))
        self._text(surface, f"Sterne gesamt: {total}/{len(LEVEL_FILES) * 3}",
                   self.small, (VIRTUAL_W - 240, 8), (255, 232, 150))
        bt = self.game.best_time(self.sel)
        if bt > 0:
            m, s = divmod(int(bt), 60)
            self._text(surface, f"Bestzeit {m}:{s:02d}", self.small,
                       (VIRTUAL_W - 240, 32), (200, 220, 245))
        self._center(surface,
                     "Links/Rechts wählen · ENTER spielen · E Editor · O Optionen · ESC Menü",
                     self.small, (215, 225, 240), VIRTUAL_H - 20)

    def _text(self, surface, text, font, pos, color):
        surface.blit(font.render(text, True, UI_SHADOW), (pos[0] + 2, pos[1] + 2))
        surface.blit(font.render(text, True, color), pos)

    def _center(self, surface, text, font, color, y):
        img = font.render(text, True, color)
        rect = img.get_rect(center=(VIRTUAL_W // 2, y))
        surface.blit(font.render(text, True, UI_SHADOW), rect.move(2, 2))
        surface.blit(img, rect)
