"""Laden von Bildern und Zerschneiden von Sprite-Strips.

Alle Loader sind fehlertolerant: fehlt eine Datei, wird eine gut sichtbare
Platzhalter-Fläche zurückgegeben, damit das Spiel niemals wegen fehlender
Assets abstürzt.
"""
from __future__ import annotations

from pathlib import Path

import pygame


def _placeholder(size: tuple[int, int], tag: str = "?") -> pygame.Surface:
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill((255, 0, 220, 255))
    pygame.draw.rect(surf, (0, 0, 0), surf.get_rect(), 1)
    return surf


def load_image(path: str | Path, size: tuple[int, int] | None = None) -> pygame.Surface:
    """Lädt ein PNG mit Alpha. Fehlt es, kommt ein Platzhalter zurück."""
    path = Path(path)
    if not path.exists():
        return _placeholder(size or (16, 16), path.stem)
    try:
        img = pygame.image.load(str(path)).convert_alpha()
    except pygame.error:
        return _placeholder(size or (16, 16), path.stem)
    if size is not None and img.get_size() != size:
        img = pygame.transform.scale(img, size)
    return img


def slice_strip(sheet: pygame.Surface, frame_w: int, frame_h: int) -> list[pygame.Surface]:
    """Zerschneidet einen horizontalen Streifen in gleich große Frames."""
    frames: list[pygame.Surface] = []
    count = sheet.get_width() // frame_w
    for i in range(count):
        rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
        frames.append(sheet.subsurface(rect).copy())
    return frames


def slice_grid(sheet: pygame.Surface, tile: int) -> list[pygame.Surface]:
    """Zerschneidet ein Grid (zeilenweise) in tile x tile Kacheln."""
    tiles: list[pygame.Surface] = []
    cols = sheet.get_width() // tile
    rows = sheet.get_height() // tile
    for ry in range(rows):
        for rx in range(cols):
            rect = pygame.Rect(rx * tile, ry * tile, tile, tile)
            tiles.append(sheet.subsurface(rect).copy())
    return tiles
