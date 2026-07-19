"""In-Game-Level-Editor (Maus + Tastatur).

Maus: links setzen (ziehen malt), rechts löschen, Mausrad Auswahl, mittlere
Taste ziehen zum Schwenken. Tastatur: Pfeile/WASD Cursor, Leertaste setzen,
Entf löschen, Tab Modus, Q/E Auswahl, Y Theme, B Startpunkt, F5 speichern,
P testspielen, L neu laden, ESC Menü.

Speichert nach <User-Daten>/levels/<datei> (Standard custom.json) – funktioniert
auch bei installierten, schreibgeschützten Builds.
"""
from __future__ import annotations

import json

import pygame

from ..engine.scene import Scene
from ..settings import (VIRTUAL_W, VIRTUAL_H, TILE, LEVEL_DIR, USER_LEVEL_DIR,
                        WHITE, UI_SHADOW)
from ..world.tilemap import CHAR_TO_TILE

TILE_PAL = [("G", "Gras"), ("D", "Erde"), ("B", "Ziegel"),
            ("#", "Hartblock"), ("S", "Stein"), ("I", "Eis")]
ENT_PAL = ["coin", "star", "growth", "snowball", "spiky", "flyer",
           "spring", "checkpoint", "mplat", "goal", "boss"]
PROP_PAL = ["bush", "tree", "cloud", "flag"]
THEMES = ["grass", "sunset", "night", "ice", "cave"]
MODES = ["tile", "entity", "prop"]

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
HUD_H = 30


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
        self.cam = [0.0, 0.0]
        self.painting = None       # 'place' | 'erase' | None
        self.panning = False
        self._load_or_blank()
        self.game.audio.play_music("title.ogg")

    # --- Modell ------------------------------------------------------
    def _blank(self):
        for x in range(W):
            self.grid[GROUND][x] = "G"
            self.grid[GROUND + 1][x] = "D"
        self.ents = [["goal", W - 4, FLOOR]]
        self.spawn = [3, FLOOR]

    def _src_path(self):
        for base in (USER_LEVEL_DIR, LEVEL_DIR):
            p = base / self.filename
            if p.exists():
                return p
        return None

    def _load_or_blank(self):
        path = self._src_path()
        if path is None:
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
        return {"name": self.name, "theme": THEMES[self.theme], "spawn": list(self.spawn),
                "solid": ["".join(r) for r in self.grid],
                "props": self.props, "entities": self.ents}

    def _save(self):
        USER_LEVEL_DIR.mkdir(parents=True, exist_ok=True)
        path = USER_LEVEL_DIR / self.filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_data(), f, ensure_ascii=False, indent=0)
        self._flash(f"Gespeichert: {path}")

    def _flash(self, msg):
        self.status, self.status_t = msg, 2.5

    def _pal_len(self):
        return [len(TILE_PAL), len(ENT_PAL), len(PROP_PAL)][self.mode]

    def _place_at(self, tx, ty):
        if not (0 <= tx < W and 0 <= ty < H):
            return
        m = MODES[self.mode]
        if m == "tile":
            self.grid[ty][tx] = TILE_PAL[self.sel][0]
        elif m == "entity":
            kind = ENT_PAL[self.sel]
            self.ents = [e for e in self.ents if not (e[1] == tx and e[2] == ty)]
            if kind == "mplat":
                self.ents.append(["mplat", tx, ty, min(W - 1, tx + 4), ty, 3])
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

    def _erase_at(self, tx, ty):
        if not (0 <= tx < W and 0 <= ty < H):
            return
        before = len(self.ents) + len(self.props)
        self.ents = [e for e in self.ents if not (e[1] == tx and e[2] == ty)]
        self.props = [p for p in self.props if not (p[1] == tx and p[2] == ty)]
        if len(self.ents) + len(self.props) == before:
            self.grid[ty][tx] = "."

    def _hovered(self):
        mvx, mvy = self.game.mouse_virtual()
        if mvy < HUD_H:
            return None
        tx = int((mvx + self.cam[0]) // TILE)
        ty = int((mvy + self.cam[1]) // TILE)
        if 0 <= tx < W and 0 <= ty < H:
            return (tx, ty)
        return None

    # --- Events ------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                h = self._hovered()
                if h:
                    self.cursor = list(h)
                    self._place_at(*h)
                    self.painting = "place"
            elif event.button == 3:
                h = self._hovered()
                if h:
                    self.cursor = list(h)
                    self._erase_at(*h)
                    self.painting = "erase"
            elif event.button == 2:
                self.panning = True
            return
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button in (1, 3):
                self.painting = None
            elif event.button == 2:
                self.panning = False
            return
        if event.type == pygame.MOUSEMOTION:
            if self.panning:
                s = self.game.view_transform()[0] or 1
                self.cam[0] -= event.rel[0] / s
                self._clamp_cam()
            elif self.painting:
                h = self._hovered()
                if h:
                    self.cursor = list(h)
                    (self._place_at if self.painting == "place" else self._erase_at)(*h)
            return
        if event.type == pygame.MOUSEWHEEL:
            self.sel = (self.sel + (1 if event.y > 0 else -1)) % self._pal_len()
            return
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
            self._place_at(*cur)
        elif k in (pygame.K_BACKSPACE, pygame.K_DELETE):
            self._erase_at(*cur)
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
            self.spawn = list(cur)
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

    def _clamp_cam(self):
        self.cam[0] = max(0.0, min(self.cam[0], W * TILE - VIRTUAL_W))
        self.cam[1] = max(0.0, min(self.cam[1], max(0, H * TILE - VIRTUAL_H)))

    def update(self, dt):
        # Kamera zum Cursor scrollen (Tastatur)
        cx = self.cursor[0] * TILE
        if cx - self.cam[0] < 5 * TILE:
            self.cam[0] = cx - 5 * TILE
        elif cx - self.cam[0] > VIRTUAL_W - 6 * TILE:
            self.cam[0] = cx - (VIRTUAL_W - 6 * TILE)
        self._clamp_cam()
        if self.status_t > 0:
            self.status_t -= dt

    # --- Zeichnen ----------------------------------------------------
    def draw(self, surface):
        surface.fill((60, 80, 110))
        ox, oy = int(self.cam[0]), int(self.cam[1])
        ts = self.game.assets.tileset
        x0 = max(0, ox // TILE)
        x1 = min(W - 1, (ox + VIRTUAL_W) // TILE)
        for ty in range(H):
            for tx in range(x0, x1 + 1):
                tid = CHAR_TO_TILE.get(self.grid[ty][tx], 0)
                if tid:
                    surface.blit(ts[tid], (tx * TILE - ox, ty * TILE - oy))
        for tx in range(x0, x1 + 2):
            x = tx * TILE - ox
            pygame.draw.line(surface, (255, 255, 255, 30), (x, 0), (x, VIRTUAL_H))
        for name, tx, ty in self.props:
            self._marker(surface, tx, ty, PROP_COLOR, name[:2], ox, oy)
        for e in self.ents:
            col, code = ENT_STYLE.get(e[0], ((220, 220, 220), "?"))
            self._marker(surface, e[1], e[2], col, code, ox, oy)
        sx, sy = self.spawn
        pygame.draw.rect(surface, (90, 230, 120),
                         (sx * TILE - ox, sy * TILE - oy, TILE, TILE), 2)
        surface.blit(self.small.render("Start", True, (90, 230, 120)),
                     (sx * TILE - ox, sy * TILE - oy - 16))
        # Cursor / Maus-Hover
        hov = self._hovered()
        if hov:
            pygame.draw.rect(surface, (120, 200, 255),
                             (hov[0] * TILE - ox, hov[1] * TILE - oy, TILE, TILE), 1)
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
        bar = pygame.Surface((VIRTUAL_W, HUD_H), pygame.SRCALPHA)
        bar.fill((10, 14, 28, 210))
        surface.blit(bar, (0, 0))
        m = MODES[self.mode]
        sel = (TILE_PAL[self.sel][1] if m == "tile"
               else ENT_PAL[self.sel] if m == "entity" else PROP_PAL[self.sel])
        info = f"Modus: {m}  |  Auswahl: {sel}  |  Theme: {THEMES[self.theme]}  |  {self.name}"
        surface.blit(self.font.render(info, True, WHITE), (8, 5))
        help1 = ("Maus: links setzen · rechts löschen · Rad Auswahl · Mitte ziehen schwenken   "
                 "|   Tab Modus · Y Theme · B Start · F5 speichern · P testen · ESC Menü")
        surface.blit(self.small.render(help1, True, UI_SHADOW), (9, VIRTUAL_H - 21))
        surface.blit(self.small.render(help1, True, (210, 220, 240)), (8, VIRTUAL_H - 22))
        if self.status_t > 0:
            s = self.small.render(self.status, True, (255, 236, 130))
            surface.blit(s, s.get_rect(center=(VIRTUAL_W // 2, 44)))
