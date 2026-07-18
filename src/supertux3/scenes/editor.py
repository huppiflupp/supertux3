"""In-Game-Level-Editor (tastaturgesteuert).

Cursor mit Pfeilen/WASD bewegen, Objekte setzen/löschen, speichern, testspielen.
Speichert nach levels/<datei> (Standard custom.json) im normalen JSON-Format,
das direkt gespielt und weiter bearbeitet werden kann.
"""
from __future__ import annotations

import json

import pygame

from ..engine.scene import Scene
from ..engine.camera import Camera
from ..settings import VIRTUAL_W, VIRTUAL_H, TILE, LEVEL_DIR, WHITE, UI_SHADOW
from ..world.tilemap import CHAR_TO_TILE

TILE_PAL = [("G", "Gras"), ("D", "Erde"), ("B", "Ziegel"),
            ("#", "Hartblock"), ("S", "Stein"), ("I", "Eis")]
ENT_PAL = ["coin", "star", "growth", "snowball", "spiky", "flyer",
           "spring", "checkpoint", "mplat", "goal", "boss"]
PROP_PAL = ["bush", "tree", "cloud", "flag"]
THEMES = ["grass", "sunset", "night", "ice", "cave"]
MODES = ["tile", "entity", "prop"]

# Marker-Farben/Kürzel für die Objektanzeige
ENT_STYLE = {
    "coin": ((255, 214, 70), "C"), "star": ((255, 236, 120), "*"),
    "growth": ((255, 244, 200), "G+"), "snowball": ((230, 240, 255), "Sn"),
    "spiky": ((214, 90, 66), "Sp"), "flyer": ((170, 140, 224), "Fl"),
    "spring": ((226, 90, 100), "^"), "checkpoint": ((110, 210, 130), "Ck"),
    "mplat": ((176, 130, 84), "<>"), "goal": ((240, 220, 90), "Ziel"),
    "boss": ((200, 220, 255), "BOSS"),
}
PROP_COLOR = (110, 200, 120)

W, H = 130, 17
GROUND = 15
FLOOR = 14


class EditorScene(Scene):
    def __init__(self, game, filename: str = "custom.json"):
        super().__init__(game)
        self.filename = filename

    def on_enter(self):
        self.font = pygame.font.Font(None, 26)
        self.small = pygame.font.Font(None, 22)
        self.cursor = [4, FLOOR]
        self.mode = 0
        self.sel = 0
        self.theme = 0
        self.name = "Mein Level"
        self.status = ""
        self.status_t = 0.0
        self.grid = [["." for _ in range(W)] for _ in range(H)]
        self.ents = []
        self.props = []
        self.spawn = [3, FLOOR]
        self._load_or_blank()
        self.camera = Camera(W * TILE, H * TILE)
        self.camera.update(self._cur_rect(), 0.0, snap=True)
        self.game.audio.play_music("title.ogg")

    # --- Modell ------------------------------------------------------
    def _blank(self):
        for x in range(W):
            self.grid[GROUND][x] = "G"
            self.grid[GROUND + 1][x] = "D"
        self.ents = [["goal", W - 4, FLOOR]]
        self.spawn = [3, FLOOR]

    def _load_or_blank(self):
        path = LEVEL_DIR / self.filename
        if not path.exists():
            self._blank()
            return
        try:
            data = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError):
            self._blank()
            return
        rows = data.get("solid", [])
        for y in range(min(H, len(rows))):
            for x in range(min(W, len(rows[y]))):
                self.grid[y][x] = rows[y][x]
        self.ents = [list(e) for e in data.get("entities", [])]
        self.props = [list(p) for p in data.get("props", [])]
        self.spawn = list(data.get("spawn", [3, FLOOR]))
        th = data.get("theme", "grass")
        self.theme = THEMES.index(th) if th in THEMES else 0
        self.name = data.get("name", "Mein Level")

    def to_data(self):
        return {
            "name": self.name, "theme": THEMES[self.theme], "spawn": list(self.spawn),
            "solid": ["".join(r) for r in self.grid],
            "props": self.props, "entities": self.ents,
        }

    def _save(self):
        path = LEVEL_DIR / self.filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_data(), f, ensure_ascii=False, indent=0)
        self._flash(f"Gespeichert: {self.filename}")

    def _flash(self, msg):
        self.status = msg
        self.status_t = 2.0

    def _cur_rect(self):
        return pygame.Rect(self.cursor[0] * TILE, self.cursor[1] * TILE, TILE, TILE)

    def _ents_at(self, tx, ty):
        return [e for e in self.ents if e[1] == tx and e[2] == ty]

    def _props_at(self, tx, ty):
        return [p for p in self.props if p[1] == tx and p[2] == ty]

    def _place(self):
        tx, ty = self.cursor
        m = MODES[self.mode]
        if m == "tile":
            self.grid[ty][tx] = TILE_PAL[self.sel][0]
        elif m == "entity":
            kind = ENT_PAL[self.sel]
            self.ents = [e for e in self.ents if not (e[1] == tx and e[2] == ty)]
            if kind == "mplat":
                self.ents.append(["mplat", tx, ty, tx + 4, ty, 3])
            elif kind == "flyer":
                self.ents.append(["flyer", tx, ty, 6])
            elif kind == "boss":
                self.ents.append(["boss", tx, ty, "frost"])
            else:
                self.ents.append([kind, tx, ty])
        else:
            name = PROP_PAL[self.sel]
            self.props = [p for p in self.props if not (p[1] == tx and p[2] == ty)]
            self.props.append([name, tx, ty])

    def _erase(self):
        tx, ty = self.cursor
        before = len(self.ents) + len(self.props)
        self.ents = [e for e in self.ents if not (e[1] == tx and e[2] == ty)]
        self.props = [p for p in self.props if not (p[1] == tx and p[2] == ty)]
        if len(self.ents) + len(self.props) == before:
            self.grid[ty][tx] = "."

    # --- Events ------------------------------------------------------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        k = event.key
        cur = self.cursor
        if k in (pygame.K_LEFT, pygame.K_a):
            cur[0] = max(0, cur[0] - 1)
        elif k in (pygame.K_RIGHT, pygame.K_d):
            cur[0] = min(W - 1, cur[0] + 1)
        elif k in (pygame.K_UP, pygame.K_w):
            cur[1] = max(0, cur[1] - 1)
        elif k in (pygame.K_DOWN, pygame.K_s):
            cur[1] = min(H - 1, cur[1] + 1)
        elif k == pygame.K_SPACE:
            self._place()
        elif k in (pygame.K_BACKSPACE, pygame.K_DELETE):
            self._erase()
        elif k == pygame.K_TAB:
            self.mode = (self.mode + 1) % len(MODES)
            self.sel = 0
        elif k == pygame.K_e:
            self.sel = (self.sel + 1) % self._pal_len()
        elif k == pygame.K_q:
            self.sel = (self.sel - 1) % self._pal_len()
        elif k == pygame.K_y:
            self.theme = (self.theme + 1) % len(THEMES)
        elif k == pygame.K_b:
            self.spawn = list(self.cursor)
            self._flash("Startpunkt gesetzt")
        elif k == pygame.K_F5:
            self._save()
        elif k == pygame.K_l:
            self.on_enter()
            self._flash("Neu geladen")
        elif k == pygame.K_p:
            self._save()
            from .play import PlayScene
            self.game.lives = 3
            self.game.scenes.switch(PlayScene(self.game, level_name=self.filename))
        elif k == pygame.K_ESCAPE:
            from .menu import MenuScene
            self.game.scenes.switch(MenuScene(self.game))

    def _pal_len(self):
        return [len(TILE_PAL), len(ENT_PAL), len(PROP_PAL)][self.mode]

    def update(self, dt):
        self.camera.update(self._cur_rect(), dt)
        if self.status_t > 0:
            self.status_t -= dt

    # --- Zeichnen ----------------------------------------------------
    def draw(self, surface):
        surface.fill((60, 80, 110))
        cam = self.camera
        ox, oy = cam.offset
        ts = self.game.assets.tileset
        # Kacheln
        for ty in range(H):
            for tx in range(W):
                ch = self.grid[ty][tx]
                tid = CHAR_TO_TILE.get(ch, 0)
                if tid:
                    surface.blit(ts[tid], (tx * TILE - ox, ty * TILE - oy))
        # Gitter
        for tx in range(W + 1):
            x = tx * TILE - ox
            if 0 <= x <= VIRTUAL_W:
                pygame.draw.line(surface, (255, 255, 255, 30), (x, 0), (x, VIRTUAL_H))
        # Props
        for name, tx, ty in self.props:
            self._marker(surface, tx, ty, PROP_COLOR, name[:2], ox, oy)
        # Entities
        for e in self.ents:
            col, code = ENT_STYLE.get(e[0], ((220, 220, 220), "?"))
            self._marker(surface, e[1], e[2], col, code, ox, oy)
        # Startpunkt
        sx, sy = self.spawn
        pygame.draw.rect(surface, (90, 230, 120),
                         (sx * TILE - ox, sy * TILE - oy, TILE, TILE), 2)
        st = self.small.render("Start", True, (90, 230, 120))
        surface.blit(st, (sx * TILE - ox, sy * TILE - oy - 16))
        # Cursor
        cx, cy = self.cursor
        pygame.draw.rect(surface, (255, 230, 90),
                         (cx * TILE - ox, cy * TILE - oy, TILE, TILE), 2)
        self._hud(surface)

    def _marker(self, surface, tx, ty, color, code, ox, oy):
        r = pygame.Rect(tx * TILE - ox + 2, ty * TILE - oy + 2, TILE - 4, TILE - 4)
        pygame.draw.rect(surface, color, r, border_radius=4)
        pygame.draw.rect(surface, (20, 24, 36), r, width=1, border_radius=4)
        img = self.small.render(code, True, (20, 24, 36))
        surface.blit(img, img.get_rect(center=r.center))

    def _hud(self, surface):
        bar = pygame.Surface((VIRTUAL_W, 30), pygame.SRCALPHA)
        bar.fill((10, 14, 28, 200))
        surface.blit(bar, (0, 0))
        m = MODES[self.mode]
        if m == "tile":
            sel = TILE_PAL[self.sel][1]
        elif m == "entity":
            sel = ENT_PAL[self.sel]
        else:
            sel = PROP_PAL[self.sel]
        info = f"Modus: {m}  |  Auswahl: {sel}  |  Theme: {THEMES[self.theme]}  |  {self.name}"
        surface.blit(self.font.render(info, True, WHITE), (8, 6))
        help1 = ("Pfeile/WASD bewegen · Leertaste setzen · Entf löschen · Tab Modus · "
                 "Q/E Auswahl · Y Theme · B Start · F5 speichern · P testen · L neu · ESC Menü")
        h = self.small.render(help1, True, (210, 220, 240))
        surface.blit(self.small.render(help1, True, UI_SHADOW), (9, VIRTUAL_H - 21))
        surface.blit(h, (8, VIRTUAL_H - 22))
        if self.status_t > 0:
            s = self.font.render(self.status, True, (255, 236, 130))
            surface.blit(s, s.get_rect(center=(VIRTUAL_W // 2, 44)))
