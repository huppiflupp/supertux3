"""Zentrales Laden aller Grafiken (Kachelsatz, Sprites, Props, Items).

Die Frame-Maße hier müssen zum Pixel-Art-Generator
(tools/asset_pipeline/gen_pixelart.py) passen.
"""
from __future__ import annotations

import pygame

from .settings import IMAGE_DIR, TILE
from .engine.spritesheet import load_image, slice_strip, slice_grid

# --- geteilte Sprite-Spezifikation (HD, 32px-Kacheln) -------------------
PENGU_FW, PENGU_FH = 40, 48
PENGU_BIG_FW, PENGU_BIG_FH = 60, 72
PENGU_LAYOUT = ["idle0", "idle1", "walk0", "walk1", "walk2", "walk3",
                "jump", "fall", "duck", "throw"]
COIN_FW, COIN_FH = 24, 24
SNOWBALL_FW, SNOWBALL_FH = 36, 32
SNOWBALL_LAYOUT = ["walk0", "walk1", "flat"]
FLYER_FW, FLYER_FH = 40, 28
SPIKY_FW, SPIKY_FH = 36, 34
SPRING_FW, SPRING_FH = 32, 24
CHECKPOINT_FW, CHECKPOINT_FH = 32, 64
BOSS_FW, BOSS_FH = 64, 60
BOSS_LAYOUT = ["walk0", "walk1", "hurt"]


def _named(frames, layout):
    return {n: frames[i] for i, n in enumerate(layout) if i < len(frames)}


class Assets:
    def __init__(self) -> None:
        self.tileset: list[pygame.Surface] = []
        self.player: dict[str, list[pygame.Surface]] = {}
        self.player_big: dict[str, list[pygame.Surface]] = {}
        self.coin: list[pygame.Surface] = []
        self.snowball: dict[str, list[pygame.Surface]] = {}
        self.flyer: list[pygame.Surface] = []
        self.spiky: list[pygame.Surface] = []
        self.props: dict[str, pygame.Surface] = {}
        self.item_grow: pygame.Surface | None = None
        self.spring: list[pygame.Surface] = []
        self.checkpoint: list[pygame.Surface] = []

    def _pengu(self, path, fw, fh):
        frames = slice_strip(load_image(path), fw, fh)
        named = _named(frames, PENGU_LAYOUT)
        d = {
            "idle": [named.get("idle0"), named.get("idle1")],
            "walk": [named.get("walk0"), named.get("walk1"), named.get("walk2"), named.get("walk3")],
            "jump": [named.get("jump")],
            "fall": [named.get("fall")],
            "duck": [named.get("duck")],
            "throw": [named.get("throw")],
        }
        return {k: [f for f in v if f is not None] or [frames[0]] for k, v in d.items()}

    def load(self) -> None:
        self.tileset = slice_grid(load_image(IMAGE_DIR / "tiles" / "tileset.png"), TILE)

        self.player = self._pengu(IMAGE_DIR / "characters" / "pengu.png", PENGU_FW, PENGU_FH)
        self.player_big = self._pengu(IMAGE_DIR / "characters" / "pengu_big.png",
                                      PENGU_BIG_FW, PENGU_BIG_FH)

        self.coin = slice_strip(load_image(IMAGE_DIR / "collectibles" / "coin.png"), COIN_FW, COIN_FH)

        sb = slice_strip(load_image(IMAGE_DIR / "enemies" / "snowball.png"), SNOWBALL_FW, SNOWBALL_FH)
        sbn = _named(sb, SNOWBALL_LAYOUT)
        self.snowball = {
            "walk": [sbn.get("walk0", sb[0]), sbn.get("walk1", sb[0])],
            "flat": [sbn.get("flat", sb[-1])],
        }
        self.flyer = slice_strip(load_image(IMAGE_DIR / "enemies" / "flyer.png"), FLYER_FW, FLYER_FH)
        self.spiky = slice_strip(load_image(IMAGE_DIR / "enemies" / "spiky.png"), SPIKY_FW, SPIKY_FH)
        bframes = slice_strip(load_image(IMAGE_DIR / "enemies" / "boss.png"), BOSS_FW, BOSS_FH)
        bn = _named(bframes, BOSS_LAYOUT)
        self.boss = {
            "walk": [bn.get("walk0", bframes[0]), bn.get("walk1", bframes[0])],
            "hurt": [bn.get("hurt", bframes[-1])],
        }
        self.iceball = load_image(IMAGE_DIR / "enemies" / "iceball.png")

        for name in ("bush", "cloud", "tree", "flag"):
            self.props[name] = load_image(IMAGE_DIR / "props" / f"{name}.png")

        self.item_grow = load_image(IMAGE_DIR / "collectibles" / "grow.png")
        self.star = load_image(IMAGE_DIR / "collectibles" / "star.png")
        self.fish = load_image(IMAGE_DIR / "collectibles" / "fish.png")
        self.turtle = load_image(IMAGE_DIR / "collectibles" / "turtle.png")
        self.giraffe = load_image(IMAGE_DIR / "collectibles" / "giraffe.png")
        self.shield = load_image(IMAGE_DIR / "collectibles" / "shield.png")
        self.plant = slice_strip(load_image(IMAGE_DIR / "enemies" / "plant.png"), 28, 28)
        self.fireball = load_image(IMAGE_DIR / "enemies" / "fireball.png")
        self.box = load_image(IMAGE_DIR / "props" / "box.png")
        self.plane = load_image(IMAGE_DIR / "props" / "plane.png")
        self.heart = load_image(IMAGE_DIR / "ui" / "heart.png")
        self.clock = load_image(IMAGE_DIR / "ui" / "clock.png")
        self.spring = slice_strip(load_image(IMAGE_DIR / "props" / "spring.png"), SPRING_FW, SPRING_FH)
        self.checkpoint = slice_strip(load_image(IMAGE_DIR / "props" / "checkpoint.png"),
                                      CHECKPOINT_FW, CHECKPOINT_FH)

    # Hintergrund je Level (Dateiname) laden – oder None
    def background(self, name: str | None) -> pygame.Surface | None:
        if not name:
            return None
        path = IMAGE_DIR / "background" / name
        return load_image(path) if path.exists() else None
