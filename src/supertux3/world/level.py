"""Level laden und die Spielwelt aufbauen.

Levelformat (JSON), Koordinaten in Kacheln:
{
  "name": "...", "theme": "grass|sunset|night|ice|cave",
  "background": "datei.png" (optional, überschreibt Theme),
  "music": "datei.ogg" (optional),
  "spawn": [tx, ty],
  "solid": ["Zeilen (siehe tilemap.CHAR_TO_TILE)"],
  "props":  [["bush", tx, ty], ...],
  "entities": [
     ["coin", tx, ty], ["snowball", tx, ty], ["spiky", tx, ty],
     ["flyer", tx, ty, patrol?], ["growth", tx, ty], ["spring", tx, ty],
     ["checkpoint", tx, ty], ["mplat", tx, ty, tx2, ty2, wtiles?], ["goal", tx, ty]
  ]
}
"""
from __future__ import annotations

import json
from pathlib import Path

import pygame

from .tilemap import Tilemap
from ..settings import TILE, LEVEL_DIR
from ..entities.player import Player, FORM
from ..entities.enemy import Snowball, Spiky, Flyer
from ..entities.collectible import Coin, GrowItem, Goal, Star
from ..entities.platform import MovingPlatform, Spring, Checkpoint
from ..entities.boss import Boss

# Theme -> (Hintergrund, Musik)
THEMES = {
    "grass":  ("sky_parallax.png", "level1.ogg"),
    "sunset": ("sunset_hills.png", "level2.ogg"),
    "night":  ("night_hills.png", "level3.ogg"),
    "ice":    ("ice_mountains.png", "ice.ogg"),
    "cave":   ("cave.png", "cave.ogg"),
}


class Level:
    def __init__(self, game, data: dict):
        self.game = game
        self.name = data.get("name", "Unbenannt")
        theme = data.get("theme", "grass")
        bg_default, music_default = THEMES.get(theme, THEMES["grass"])
        self.background_name = data.get("background", bg_default)
        self.music = data.get("music", music_default)
        self.tilemap = Tilemap(data.get("solid", []), game.assets.tileset, TILE)

        sx, sy = data.get("spawn", [2, 2])
        self.spawn_px = (sx * TILE, (sy + 1) * TILE)
        self.player = Player(sx * TILE, (sy + 1) * TILE - FORM["small"][3], game.assets)

        self.coins: list[Coin] = []
        self.items: list[GrowItem] = []
        self.stars: list[Star] = []
        self.stars_collected = 0
        self.enemies: list = []
        self.springs: list[Spring] = []
        self.checkpoints: list[Checkpoint] = []
        self.platforms: list[MovingPlatform] = []
        self.projectiles: list = []
        self.boss = None
        self.goal: Goal | None = None

        A = game.assets
        for e in data.get("entities", []):
            k = e[0]
            if k == "coin":
                self.coins.append(Coin(e[1] * TILE + (TILE - 24) // 2,
                                       e[2] * TILE + (TILE - 24) // 2, A))
            elif k == "growth":
                iw = A.item_grow.get_width()
                self.items.append(GrowItem(e[1] * TILE + (TILE - iw) // 2,
                                           e[2] * TILE + (TILE - iw) // 2, A))
            elif k == "star":
                sw = A.star.get_width()
                self.stars.append(Star(e[1] * TILE + (TILE - sw) // 2,
                                       e[2] * TILE + (TILE - sw) // 2, A))
            elif k == "snowball":
                s = Snowball(e[1] * TILE, 0, A); s.y = (e[2] + 1) * TILE - s.h
                self.enemies.append(s)
            elif k == "spiky":
                s = Spiky(e[1] * TILE, 0, A); s.y = (e[2] + 1) * TILE - s.h
                self.enemies.append(s)
            elif k == "flyer":
                patrol = e[3] if len(e) > 3 else 6
                self.enemies.append(Flyer(e[1] * TILE, e[2] * TILE, A, patrol))
            elif k == "spring":
                self.springs.append(Spring(e[1] * TILE, (e[2] + 1) * TILE, A))
            elif k == "checkpoint":
                self.checkpoints.append(Checkpoint(e[1] * TILE, (e[2] + 1) * TILE, A))
            elif k == "mplat":
                x2 = e[3] if len(e) > 3 else e[1]
                y2 = e[4] if len(e) > 4 else e[2]
                wt = e[5] if len(e) > 5 else 3
                self.platforms.append(MovingPlatform(e[1] * TILE, e[2] * TILE,
                                                     x2 * TILE, y2 * TILE, wt))
            elif k == "boss":
                variant = e[3] if len(e) > 3 else "frost"
                self.boss = Boss(e[1] * TILE, (e[2] + 1) * TILE, A, variant)
                self.enemies.append(self.boss)
            elif k == "goal":
                self.goal = Goal(e[1] * TILE, (e[2] + 1) * TILE, A)

        self.props: list[tuple[pygame.Surface, int, int]] = []
        for p in data.get("props", []):
            img = A.props.get(p[0])
            if img:
                self.props.append((img, p[1] * TILE, (p[2] + 1) * TILE - img.get_height()))

        self.total_coins = len(self.coins)
        self.total_stars = len(self.stars)

    def platform_rects(self):
        return [p.rect for p in self.platforms]

    @property
    def width_px(self) -> int:
        return self.tilemap.width_px

    @property
    def height_px(self) -> int:
        return self.tilemap.height_px

    @classmethod
    def load(cls, game, name: str) -> "Level":
        path = Path(name)
        if not path.exists():
            path = LEVEL_DIR / name
        if path.suffix.lower() == ".tmx":
            from .tmx import parse_tmx
            data = parse_tmx(path)
        else:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        return cls(game, data)
