#!/usr/bin/env python3
"""Prozeduraler Pixel-Art-Generator für SuperTux3.

Erzeugt spielfertige, konsistente Sprites/Kacheln in der internen Auflösung
(16-px-Kacheln). Das Spiel skaliert alles per Nearest-Neighbor hoch, daher wird
hier bewusst in Zielgröße (klein) gezeichnet, nicht herunterskaliert.

Ausgabe -> assets/images/{tiles,characters,collectibles,enemies,props}/

Die Frame-Maße müssen zu src/supertux3/assets.py passen:
  pengu  : 9 Frames à 20x24  (idle0,idle1,walk0-3,jump,fall,duck)
  coin   : 6 Frames à 12x12
  snowball: 3 Frames à 18x16 (walk0,walk1,flat)
  tileset: 7 Kacheln à 16x16 (0=leer .. 6)
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "assets" / "images"

# --- Palette -------------------------------------------------------------
BODY = (34, 38, 52, 255)
BODY_HI = (58, 64, 84, 255)
BELLY = (245, 248, 255, 255)
ORANGE = (255, 176, 46, 255)
ORANGE_D = (214, 122, 22, 255)
SCARF = (222, 66, 74, 255)
SCARF_D = (176, 42, 52, 255)
WHITE = (255, 255, 255, 255)
PUP = (24, 26, 36, 255)
NONE = (0, 0, 0, 0)


def _save(img: Image.Image, sub: str, name: str) -> None:
    d = IMG / sub
    d.mkdir(parents=True, exist_ok=True)
    img.save(d / name)
    print(f"  {sub}/{name}  {img.size}")


# =========================================================================
#  Spieler „Pengu"
# =========================================================================
def draw_pengu(lfoot: int = 0, rfoot: int = 0, arms_up: bool = False,
               squash: int = 0, blink: bool = False) -> Image.Image:
    img = Image.new("RGBA", (20, 24), NONE)
    d = ImageDraw.Draw(img)
    top = 2 + squash
    bottom = 22

    # Flossen (Arme)
    ay = top + 7 - (5 if arms_up else 0)
    d.ellipse([1, ay, 5, ay + 7], fill=BODY)
    d.ellipse([14, ay, 18, ay + 7], fill=BODY)

    # Körper + Kopf als eine Silhouette
    d.ellipse([3, top, 16, bottom], fill=BODY)
    d.ellipse([4, top, 15, top + 10], fill=BODY)
    # leichte Aufhellung oben
    d.ellipse([6, top + 1, 12, top + 5], fill=BODY_HI)

    # Bauch
    d.ellipse([6, top + 8, 13, bottom - 1], fill=BELLY)

    # Augen
    ey = top + 4
    if blink:
        d.line([7, ey + 1, 9, ey + 1], fill=PUP)
        d.line([11, ey + 1, 13, ey + 1], fill=PUP)
    else:
        d.ellipse([7, ey, 9, ey + 3], fill=WHITE)
        d.ellipse([11, ey, 13, ey + 3], fill=WHITE)
        d.point([(8, ey + 1), (12, ey + 1)], fill=PUP)

    # Schnabel
    by = top + 6
    d.polygon([(9, by), (12, by + 1), (9, by + 3)], fill=ORANGE)
    d.point([(9, by + 1)], fill=ORANGE_D)

    # Schal (macht Pengu unverwechselbar)
    sy = top + 7
    d.rectangle([4, sy, 15, sy + 1], fill=SCARF)
    d.rectangle([13, sy + 1, 15, sy + 4], fill=SCARF_D)

    # Füße
    d.rectangle([5 + lfoot, bottom, 8 + lfoot, bottom + 1], fill=ORANGE)
    d.rectangle([11 + rfoot, bottom, 14 + rfoot, bottom + 1], fill=ORANGE)
    return img


def gen_pengu() -> None:
    frames = [
        draw_pengu(0, 0),                       # idle0
        draw_pengu(0, 0, squash=0, blink=True), # idle1 (blinzeln)
        draw_pengu(-1, 2),                      # walk0
        draw_pengu(0, 0),                       # walk1
        draw_pengu(2, -1),                      # walk2
        draw_pengu(0, 0),                       # walk3
        draw_pengu(1, 1, arms_up=True),         # jump
        draw_pengu(-2, 2, arms_up=False),       # fall
        draw_pengu(0, 0, squash=4),             # duck
    ]
    sheet = Image.new("RGBA", (20 * len(frames), 24), NONE)
    for i, f in enumerate(frames):
        sheet.paste(f, (i * 20, 0))
    _save(sheet, "characters", "pengu.png")


# =========================================================================
#  Münze
# =========================================================================
def gen_coin() -> None:
    GOLD = (255, 214, 64, 255)
    GOLD_D = (214, 158, 30, 255)
    GOLD_HI = (255, 246, 190, 255)
    frames = []
    widths = [12, 9, 5, 2, 5, 9]   # Rotationsillusion
    for w in widths:
        img = Image.new("RGBA", (12, 12), NONE)
        d = ImageDraw.Draw(img)
        cx = 6
        x0 = cx - w / 2
        x1 = cx + w / 2
        d.ellipse([x0, 1, x1, 10], fill=GOLD, outline=GOLD_D)
        if w >= 5:
            d.ellipse([x0 + 1, 3, x1 - 1, 8], outline=GOLD_HI)
            d.point([(cx - 1, 3)], fill=GOLD_HI)
        frames.append(img)
    sheet = Image.new("RGBA", (12 * len(frames), 12), NONE)
    for i, f in enumerate(frames):
        sheet.paste(f, (i * 12, 0))
    _save(sheet, "collectibles", "coin.png")


# =========================================================================
#  Gegner „Schneeball"
# =========================================================================
def draw_snowball(step: int) -> Image.Image:
    img = Image.new("RGBA", (18, 16), NONE)
    d = ImageDraw.Draw(img)
    SNOW = (238, 245, 255, 255)
    SNOW_D = (190, 205, 228, 255)
    d.ellipse([2, 2, 15, 15], fill=SNOW, outline=SNOW_D)
    d.ellipse([4, 4, 9, 9], fill=WHITE)
    # Augen
    d.ellipse([6, 6, 8, 9], fill=WHITE, outline=PUP)
    d.ellipse([10, 6, 12, 9], fill=WHITE, outline=PUP)
    d.point([(7, 8), (11, 8)], fill=PUP)
    # Mund
    d.arc([7, 9, 11, 12], 0, 180, fill=PUP)
    # Füße
    fo = 1 if step == 0 else -1
    d.rectangle([4, 14, 7, 15], fill=ORANGE_D)
    d.rectangle([10 + fo, 14, 13 + fo, 15], fill=ORANGE_D)
    return img


def draw_snowball_flat() -> Image.Image:
    img = Image.new("RGBA", (18, 16), NONE)
    d = ImageDraw.Draw(img)
    SNOW = (238, 245, 255, 255)
    SNOW_D = (190, 205, 228, 255)
    d.ellipse([1, 10, 16, 15], fill=SNOW, outline=SNOW_D)
    d.line([6, 12, 7, 12], fill=PUP)
    d.line([10, 12, 11, 12], fill=PUP)
    return img


def gen_snowball() -> None:
    frames = [draw_snowball(0), draw_snowball(1), draw_snowball_flat()]
    sheet = Image.new("RGBA", (18 * len(frames), 16), NONE)
    for i, f in enumerate(frames):
        sheet.paste(f, (i * 18, 0))
    _save(sheet, "enemies", "snowball.png")


# =========================================================================
#  Kachelsatz
# =========================================================================
def _noise_rect(d, box, base, dark, seed=0):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=base)
    n = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            n = (n * 1103515245 + 12345 + x * 7 + y * 13 + seed) & 0x7FFFFFFF
            if n % 7 == 0:
                d.point([(x, y)], fill=dark)


def gen_tileset() -> None:
    T = 16
    tiles = 7
    sheet = Image.new("RGBA", (T * tiles, T), NONE)

    def cell(i):
        img = Image.new("RGBA", (T, T), NONE)
        return img, ImageDraw.Draw(img)

    # 0: leer -> transparent
    imgs = [Image.new("RGBA", (T, T), NONE)]

    # 1: Gras-Oberseite
    img, d = cell(1)
    _noise_rect(d, (0, 4, T, T), (134, 96, 58, 255), (110, 78, 46, 255), 1)
    d.rectangle([0, 0, T, 4], fill=(94, 190, 78, 255))
    d.rectangle([0, 4, T, 5], fill=(70, 158, 60, 255))
    for x in range(0, T, 3):
        d.line([x, 4, x, 1], fill=(120, 214, 96, 255))
    imgs.append(img)

    # 2: Erde
    img, d = cell(2)
    _noise_rect(d, (0, 0, T, T), (134, 96, 58, 255), (110, 78, 46, 255), 2)
    imgs.append(img)

    # 3: Ziegel
    img, d = cell(3)
    d.rectangle([0, 0, T, T], fill=(178, 92, 66, 255))
    d.line([0, 8, T, 8], fill=(120, 60, 44, 255))
    d.line([8, 0, 8, 8], fill=(120, 60, 44, 255))
    d.line([4, 8, 4, T], fill=(120, 60, 44, 255))
    d.line([12, 8, 12, T], fill=(120, 60, 44, 255))
    imgs.append(img)

    # 4: Hartblock (metallisch)
    img, d = cell(4)
    d.rectangle([0, 0, T, T], fill=(150, 156, 170, 255))
    d.rectangle([1, 1, T - 2, T - 2], outline=(196, 202, 214, 255))
    for c in ((2, 2), (12, 2), (2, 12), (12, 12)):
        d.ellipse([c[0], c[1], c[0] + 2, c[1] + 2], fill=(96, 102, 116, 255))
    imgs.append(img)

    # 5: Stein
    img, d = cell(5)
    _noise_rect(d, (0, 0, T, T), (120, 124, 134, 255), (96, 100, 110, 255), 5)
    d.line([0, 0, T, 0], fill=(150, 154, 164, 255))
    imgs.append(img)

    # 6: Eis
    img, d = cell(6)
    d.rectangle([0, 0, T, T], fill=(176, 224, 246, 255))
    d.line([2, 2, 6, 6], fill=WHITE)
    d.line([9, 4, 12, 7], fill=(230, 246, 255, 255))
    imgs.append(img)

    for i, im in enumerate(imgs):
        sheet.paste(im, (i * T, 0))
    _save(sheet, "tiles", "tileset.png")


# =========================================================================
#  Dekor-Props
# =========================================================================
def gen_props() -> None:
    # Busch
    img = Image.new("RGBA", (24, 16), NONE)
    d = ImageDraw.Draw(img)
    for cx, cy, r in [(7, 10, 6), (13, 8, 7), (18, 11, 5)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(70, 168, 74, 255))
    d.ellipse([9, 4, 17, 12], fill=(96, 196, 96, 255))
    _save(img, "props", "bush.png")

    # Wolke
    img = Image.new("RGBA", (48, 24), NONE)
    d = ImageDraw.Draw(img)
    for cx, cy, r in [(14, 16, 8), (24, 12, 11), (34, 16, 8), (22, 18, 10)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 235))
    _save(img, "props", "cloud.png")

    # Baum
    img = Image.new("RGBA", (32, 48), NONE)
    d = ImageDraw.Draw(img)
    d.rectangle([14, 30, 19, 48], fill=(120, 82, 50, 255))
    d.ellipse([2, 2, 30, 34], fill=(60, 158, 68, 255))
    d.ellipse([6, 0, 26, 22], fill=(84, 186, 88, 255))
    _save(img, "props", "tree.png")

    # Zielfahne
    img = Image.new("RGBA", (16, 48), NONE)
    d = ImageDraw.Draw(img)
    d.rectangle([3, 0, 4, 46], fill=(210, 214, 224, 255))
    d.polygon([(5, 2), (15, 6), (5, 11)], fill=(230, 70, 80, 255))
    d.ellipse([1, 44, 12, 48], fill=(120, 90, 60, 255))
    _save(img, "props", "flag.png")


def main() -> None:
    print("Erzeuge Pixel-Art ->", IMG)
    gen_tileset()
    gen_pengu()
    gen_coin()
    gen_snowball()
    gen_props()
    print("Fertig.")


if __name__ == "__main__":
    main()
