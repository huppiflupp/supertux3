"""Zentrales Laden aller Grafiken (Kachelsatz, Sprites, Props, Hintergrund).

Die Frame-Maße hier müssen zum Pixel-Art-Generator
(tools/asset_pipeline/gen_pixelart.py) passen. Beide Seiten teilen sich die
folgende Spezifikation.
"""
from __future__ import annotations

import pygame

from .settings import IMAGE_DIR, TILE
from .engine.spritesheet import load_image, slice_strip, slice_grid

# --- geteilte Sprite-Spezifikation (HD, 32px-Kacheln) -------------------
PENGU_FW, PENGU_FH = 40, 48
# Reihenfolge der Frames im Streifen characters/pengu.png
PENGU_LAYOUT = ["idle0", "idle1", "walk0", "walk1", "walk2", "walk3", "jump", "fall", "duck"]
COIN_FW, COIN_FH = 24, 24
COIN_FRAMES = 6
SNOWBALL_FW, SNOWBALL_FH = 36, 32
SNOWBALL_LAYOUT = ["walk0", "walk1", "flat"]


class Assets:
    def __init__(self) -> None:
        self.tileset: list[pygame.Surface] = []
        self.player: dict[str, list[pygame.Surface]] = {}
        self.coin: list[pygame.Surface] = []
        self.snowball: dict[str, list[pygame.Surface]] = {}
        self.props: dict[str, pygame.Surface] = {}
        self.background: pygame.Surface | None = None
        self.hills: pygame.Surface | None = None

    def load(self) -> None:
        # Kachelsatz (eine Reihe 16x16-Kacheln)
        ts = load_image(IMAGE_DIR / "tiles" / "tileset.png")
        self.tileset = slice_grid(ts, TILE)

        # Spieler
        sheet = load_image(IMAGE_DIR / "characters" / "pengu.png")
        frames = slice_strip(sheet, PENGU_FW, PENGU_FH)
        named = {name: frames[i] for i, name in enumerate(PENGU_LAYOUT) if i < len(frames)}
        self.player = {
            "idle": [named.get("idle0"), named.get("idle1")],
            "walk": [named.get("walk0"), named.get("walk1"), named.get("walk2"), named.get("walk3")],
            "jump": [named.get("jump")],
            "fall": [named.get("fall")],
            "duck": [named.get("duck")],
        }
        self.player = {k: [f for f in v if f is not None] or [frames[0]] for k, v in self.player.items()}

        # Münze
        coin_sheet = load_image(IMAGE_DIR / "collectibles" / "coin.png")
        self.coin = slice_strip(coin_sheet, COIN_FW, COIN_FH) or [coin_sheet]

        # Gegner (Schneeball)
        sb = load_image(IMAGE_DIR / "enemies" / "snowball.png")
        sb_frames = slice_strip(sb, SNOWBALL_FW, SNOWBALL_FH)
        sbn = {name: sb_frames[i] for i, name in enumerate(SNOWBALL_LAYOUT) if i < len(sb_frames)}
        self.snowball = {
            "walk": [sbn.get("walk0", sb_frames[0]), sbn.get("walk1", sb_frames[0])],
            "flat": [sbn.get("flat", sb_frames[-1])],
        }

        # Props (rein dekorativ)
        for name in ("bush", "cloud", "tree", "flag"):
            self.props[name] = load_image(IMAGE_DIR / "props" / f"{name}.png")

        # Hintergrund (kann von der ComfyUI/FLUX-Pipeline stammen)
        bg = IMAGE_DIR / "background" / "sky_parallax.png"
        self.background = load_image(bg) if bg.exists() else None
        hills = IMAGE_DIR / "background" / "hills_midground.png"
        self.hills = load_image(hills) if hills.exists() else None
