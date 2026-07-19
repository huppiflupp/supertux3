"""Kachel-Welt: Kollision und Darstellung.

Die Solid-Ebene ist ein Gitter aus Kachel-IDs. ID 0 ist leer; alle anderen IDs
sind fest (Kollision) und verweisen zugleich auf den Index im Kachelsatz-Bild.
"""
from __future__ import annotations

from collections.abc import Iterator

import pygame

from ..settings import TILE

# Zeichen im Levelformat -> Kachel-ID (== Index im Kachelsatz)
CHAR_TO_TILE: dict[str, int] = {
    ".": 0, " ": 0,
    "G": 1,   # Gras-Oberseite
    "D": 2,   # Erde
    "B": 3,   # Ziegel
    "#": 4,   # Hartblock
    "S": 5,   # Stein / Fels
    "I": 6,   # Eis (etwas rutschig – optional)
    "A": 7,   # Sand-Oberseite (Wüste)
    "W": 8,   # Sandstein (Blöcke / Pyramiden)
    "M": 9,   # Mondgestein (Weltraum)
    "P": 10,  # Metallplatte (Raumstation)
    "C": 11,  # Asphalt / Straße (Stadt)
    "K": 12,  # Beton / Stahlträger (Baustelle)
    "/": 13,  # Schräge steigend-rechts
    "\\": 14, # Schräge steigend-links
}
SOLID_IDS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
# Schrägen sind NICHT im AABB-Sinn solide, sondern werden speziell aufgelöst:
# id -> Richtung (+1 = steigt nach rechts "/", -1 = steigt nach links "\")
SLOPE_DIR = {13: 1, 14: -1}


class Tilemap:
    def __init__(self, rows: list[str], tileset: list[pygame.Surface], tile: int = TILE):
        self.tile = tile
        self.height = len(rows)
        self.width = max((len(r) for r in rows), default=0)
        self.tileset = tileset
        self.grid: list[list[int]] = []
        for r in rows:
            row: list[int] = []
            for x in range(self.width):
                ch = r[x] if x < len(r) else "."
                row.append(CHAR_TO_TILE.get(ch, 0))
            self.grid.append(row)

    # --- Maße --------------------------------------------------------
    @property
    def width_px(self) -> int:
        return self.width * self.tile

    @property
    def height_px(self) -> int:
        return self.height * self.tile

    # --- Abfragen ----------------------------------------------------
    def tile_id(self, tx: int, ty: int) -> int:
        if 0 <= ty < self.height and 0 <= tx < self.width:
            return self.grid[ty][tx]
        return 0

    def is_solid(self, tx: int, ty: int) -> bool:
        return self.tile_id(tx, ty) in SOLID_IDS

    def solid_rects_around(self, rect: pygame.Rect) -> Iterator[pygame.Rect]:
        """Liefert die festen Kachel-Rechtecke, die `rect` überlappen könnten."""
        t = self.tile
        x0 = max(0, rect.left // t - 1)
        x1 = min(self.width - 1, rect.right // t + 1)
        y0 = max(0, rect.top // t - 1)
        y1 = min(self.height - 1, rect.bottom // t + 1)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if self.grid[ty][tx] in SOLID_IDS:
                    yield pygame.Rect(tx * t, ty * t, t, t)

    # --- Darstellung -------------------------------------------------
    def draw(self, surface: pygame.Surface, camera) -> None:
        t = self.tile
        ox, oy = camera.offset
        vw, vh = surface.get_size()
        x0 = max(0, ox // t)
        x1 = min(self.width - 1, (ox + vw) // t)
        y0 = max(0, oy // t)
        y1 = min(self.height - 1, (oy + vh) // t)
        blit = surface.blit
        tileset = self.tileset
        n = len(tileset)
        for ty in range(y0, y1 + 1):
            row = self.grid[ty]
            py = ty * t - oy
            for tx in range(x0, x1 + 1):
                tid = row[tx]
                if tid and tid < n:
                    blit(tileset[tid], (tx * t - ox, py))
