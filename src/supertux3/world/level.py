"""Level laden und die Spielwelt aufbauen.

Levelformat (JSON), Koordinaten in Kacheln:
{
  "name": "Grüne Hügel 1",
  "music": "level1.ogg",
  "spawn": [tx, ty],
  "solid": ["Zeilen aus Zeichen (siehe tilemap.CHAR_TO_TILE)"],
  "props":  [["bush", tx, ty], ...],          # dekorativ, unten bündig
  "entities": [["coin", tx, ty], ["snowball", tx, ty], ["goal", tx, ty]]
}
"""
from __future__ import annotations

import json
from pathlib import Path

import pygame

from .tilemap import Tilemap
from ..settings import TILE, LEVEL_DIR
from ..entities.player import Player, HITBOX_H
from ..entities.enemy import Snowball
from ..entities.collectible import Coin, Goal


class Level:
    def __init__(self, game, data: dict):
        self.game = game
        self.name = data.get("name", "Unbenannt")
        self.music = data.get("music")
        self.tilemap = Tilemap(data.get("solid", []), game.assets.tileset, TILE)

        sx, sy = data.get("spawn", [2, 2])
        self.spawn_px = (sx * TILE, (sy + 1) * TILE)
        self.player = Player(sx * TILE, (sy + 1) * TILE - HITBOX_H, game.assets)

        self.coins: list[Coin] = []
        self.enemies: list[Snowball] = []
        self.goal: Goal | None = None
        for ent in data.get("entities", []):
            kind, tx, ty = ent[0], ent[1], ent[2]
            if kind == "coin":
                self.coins.append(Coin(tx * TILE + (TILE - 12) // 2,
                                       ty * TILE + (TILE - 12) // 2, game.assets))
            elif kind == "snowball":
                sb = Snowball(tx * TILE, 0, game.assets)
                sb.y = (ty + 1) * TILE - sb.h
                self.enemies.append(sb)
            elif kind == "goal":
                self.goal = Goal(tx * TILE, (ty + 1) * TILE, game.assets)

        # Dekor-Props (Bild, x, y unten bündig)
        self.props: list[tuple[pygame.Surface, int, int]] = []
        for p in data.get("props", []):
            name, tx, ty = p[0], p[1], p[2]
            img = game.assets.props.get(name)
            if img:
                self.props.append((img, tx * TILE, (ty + 1) * TILE - img.get_height()))

        self.total_coins = len(self.coins)

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
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(game, data)
