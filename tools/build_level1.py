#!/usr/bin/env python3
"""Baut levels/level1.json ('Grüne Hügel 1') deterministisch auf.

Koordinaten in Kacheln. Boden liegt auf Reihe 15 (Gras) / 16 (Erde).
Eine Entity/ein Prop 'auf dem Boden' bekommt ty=14 (die Kachel darüber).
"""
from __future__ import annotations

import json
from pathlib import Path

W, H = 150, 17
GROUND = 15          # Gras-Reihe
FLOOR_TY = 14        # 'stehend auf Boden'
ROOT = Path(__file__).resolve().parents[1]

grid = [["." for _ in range(W)] for _ in range(H)]


def put(x, y, ch):
    if 0 <= y < H and 0 <= x < W:
        grid[y][x] = ch


def ground(x0, x1):
    for x in range(x0, x1 + 1):
        put(x, GROUND, "G")
        put(x, GROUND + 1, "D")


def platform(x0, x1, y, ch="B"):
    for x in range(x0, x1 + 1):
        put(x, y, ch)


def stair(x0, height, ch="D", top="G"):
    """Treppe aufwärts nach rechts."""
    for i in range(height):
        x = x0 + i
        for y in range(GROUND - i, GROUND + 2):
            put(x, y, ch)
        put(x, GROUND - i, top)


# --- Boden mit Abgründen -------------------------------------------------
pits = [(31, 34), (63, 66), (98, 101)]
x = 0
for a, b in pits:
    ground(x, a - 1)
    x = b + 1
ground(x, W - 1)

# --- Schwebeplattformen --------------------------------------------------
platform(18, 22, 11)
platform(26, 28, 9)
platform(44, 49, 10)
platform(54, 56, 8)
platform(72, 77, 11)
platform(85, 88, 9)
platform(110, 114, 10)
# Steinsäulen als Hindernis
platform(120, 120, GROUND - 1, "S")
platform(121, 121, GROUND - 2, "S")

# --- Treppe hoch zum Ziel ------------------------------------------------
stair(128, 4)
platform(132, 145, GROUND - 4)  # obere Ebene bis zum Ziel

entities = []
# Münzen: Bögen und Reihen
def coin_row(x0, x1, y):
    for cx in range(x0, x1 + 1):
        entities.append(["coin", cx, y])

def coin_arc(cx, y):
    entities.append(["coin", cx - 1, y])
    entities.append(["coin", cx, y - 1])
    entities.append(["coin", cx + 1, y])

coin_row(6, 9, 12)
coin_arc(32, 12)            # über 1. Abgrund
coin_row(19, 21, 9)         # über Plattform 18-22
coin_arc(64, 12)            # über 2. Abgrund
coin_row(45, 48, 8)
coin_arc(99, 12)            # über 3. Abgrund
coin_row(72, 76, 9)
coin_row(133, 138, GROUND - 5)
coin_arc(112, 8)

# Gegner auf flachen Strecken
for ex in (14, 40, 58, 82, 106, 138):
    entities.append(["snowball", ex, FLOOR_TY])

# Ziel
entities.append(["goal", 146, GROUND - 4])

# --- Dekor ---------------------------------------------------------------
props = []
for tx in (5, 24, 52, 90, 125):
    props.append(["bush", tx, FLOOR_TY])
for tx in (10, 48, 108):
    props.append(["tree", tx, FLOOR_TY])
for tx, ty in [(12, 2), (30, 1), (50, 3), (75, 2), (100, 1), (130, 2)]:
    props.append(["cloud", tx, ty])

data = {
    "name": "Grüne Hügel 1",
    "music": "level1.ogg",
    "spawn": [2, FLOOR_TY],
    "solid": ["".join(row) for row in grid],
    "props": props,
    "entities": entities,
}

out = ROOT / "levels" / "level1.json"
out.parent.mkdir(exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=0)
print(f"geschrieben: {out}  ({W}x{H}, {len(entities)} Entities, {len(props)} Props)")
