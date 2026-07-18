#!/usr/bin/env python3
"""HD-Grafik-Generator für SuperTux3 (32-px-Kacheln, SuperTux2-orientiert).

Gezeichnet wird supersampled (4x) und geglättet heruntergerechnet -> weiche,
schattierte Cartoon-Grafik statt harter Pixel. Alle Designs sind eigenständig
(kein SuperTux2-Asset wird kopiert).

Ausgabe -> assets/images/{tiles,characters,collectibles,enemies,props}/

Frame-Maße (müssen zu src/supertux3/assets.py passen):
  pengu   : 9 Frames à 40x48
  coin    : 6 Frames à 24x24
  snowball: 3 Frames à 36x32
  tileset : 7 Kacheln à 32x32 (0=leer .. 6)
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "assets" / "images"
SS = 4  # Supersampling

# --- Palette -------------------------------------------------------------
OUT = (20, 22, 32, 255)          # Kontur
BODY = (40, 46, 66, 255)
BODY_LO = (26, 30, 46, 255)
BODY_HI = (74, 84, 112, 255)
BELLY = (247, 250, 255, 255)
BELLY_SH = (206, 216, 234, 255)
BEAK = (255, 178, 44, 255)
BEAK_HI = (255, 214, 130, 255)
BEAK_LO = (210, 120, 22, 255)
SCARF = (226, 64, 72, 255)
SCARF_LO = (174, 40, 52, 255)
SCARF_HI = (246, 122, 122, 255)
FOOT = (255, 170, 40, 255)
FOOT_LO = (208, 116, 20, 255)
WHITE = (255, 255, 255, 255)
PUP = (26, 28, 40, 255)
NONE = (0, 0, 0, 0)


class Pen:
    """Zeichnet in Zielkoordinaten, intern supersampled; result() glättet."""

    def __init__(self, w: int, h: int, ss: int = SS):
        self.w, self.h, self.ss = w, h, ss
        self.img = Image.new("RGBA", (w * ss, h * ss), NONE)
        self.d = ImageDraw.Draw(self.img)

    def _b(self, box):
        return [v * self.ss for v in box]

    def _p(self, pts):
        return [(x * self.ss, y * self.ss) for x, y in pts]

    def ellipse(self, box, **kw):
        self.d.ellipse(self._b(box), **kw)

    def rect(self, box, **kw):
        self.d.rectangle(self._b(box), **kw)

    def rounded(self, box, r, **kw):
        self.d.rounded_rectangle(self._b(box), radius=r * self.ss, **kw)

    def poly(self, pts, **kw):
        self.d.polygon(self._p(pts), **kw)

    def line(self, pts, width=1, **kw):
        self.d.line(self._p(pts), width=int(width * self.ss), **kw)

    def arc(self, box, a, b, width=1, **kw):
        self.d.arc(self._b(box), a, b, width=int(width * self.ss), **kw)

    def result(self) -> Image.Image:
        return self.img.resize((self.w, self.h), Image.LANCZOS)


def _lcg(seed):
    x = seed & 0x7FFFFFFF
    while True:
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        yield x / 0x7FFFFFFF


def _save(img: Image.Image, sub: str, name: str) -> None:
    d = IMG / sub
    d.mkdir(parents=True, exist_ok=True)
    img.save(d / name)
    print(f"  {sub}/{name}  {img.size}")


def _sheet(frames, fw, fh):
    sheet = Image.new("RGBA", (fw * len(frames), fh), NONE)
    for i, f in enumerate(frames):
        sheet.paste(f, (i * fw, 0), f)
    return sheet


# =========================================================================
#  Spieler „Pengu"  (40x48)
# =========================================================================
def draw_pengu(lf=0.0, rf=0.0, llift=0.0, rlift=0.0, arms_up=False,
               squash=0.0, blink=False, breathe=0.0) -> Image.Image:
    p = Pen(40, 48)
    top = 5 + squash - breathe
    bot = 46

    # Flossen
    ay = top + 8 - (7 if arms_up else 0)
    for fx0, fx1 in ((2.5, 8), (32, 37.5)):
        p.ellipse([fx0 - .8, ay - .8, fx1 + .8, ay + 14 + .8], fill=OUT)
        p.ellipse([fx0, ay, fx1, ay + 14], fill=BODY)
        p.ellipse([fx0 + .5, ay + 1, fx1 - 1.5, ay + 8], fill=BODY_HI)

    # Körper-Silhouette + Kontur
    p.ellipse([5, top - 1, 35, bot + 1], fill=OUT)
    p.ellipse([6, top, 34, bot], fill=BODY)
    # untere Schattierung
    p.ellipse([7, top + 20, 33, bot - 1], fill=BODY_LO)
    p.ellipse([6.5, top, 34, bot - 6], fill=BODY)  # überdeckt Schatten oben wieder
    # Kopf-Glanz
    p.ellipse([11, top + 2, 24, top + 15], fill=BODY_HI)

    # Bauch
    p.ellipse([11, top + 13, 30, bot - 1], fill=BELLY)
    p.ellipse([11.5, top + 15, 20, bot - 2], fill=BELLY_SH)   # linker Schatten
    p.ellipse([13.5, top + 14, 30, bot - 1], fill=BELLY)      # rechts wieder hell

    # Augen (Blick leicht nach vorn/rechts)
    ey = top + 8
    if blink:
        p.line([(15, ey + 2), (19, ey + 2)], width=1.4, fill=PUP)
        p.line([(23, ey + 2), (27, ey + 2)], width=1.4, fill=PUP)
    else:
        for ex in (17, 25):
            p.ellipse([ex - 3, ey - 3.5, ex + 3, ey + 3.5], fill=WHITE)
            p.ellipse([ex - 3, ey - 3.5, ex + 3, ey + 3.5], outline=(120, 130, 150, 255))
            p.ellipse([ex - .5, ey - 1.5, ex + 2.5, ey + 2.5], fill=PUP)
            p.ellipse([ex + .3, ey - 1, ex + 1.6, ey + .3], fill=WHITE)

    # Schnabel
    by = top + 12
    p.poly([(19, by - 1), (26, by + 2), (19, by + 5)], fill=BEAK)
    p.poly([(19, by + 1.5), (26, by + 2), (19, by + 5)], fill=BEAK_LO)
    p.line([(19.5, by), (24.5, by + 1.8)], width=.8, fill=BEAK_HI)

    # Schal (Markenzeichen)
    sy = top + 15
    p.rounded([7, sy, 33, sy + 4.5], 2, fill=SCARF)
    p.line([(8, sy + 1), (32, sy + 1)], width=.8, fill=SCARF_HI)
    p.poly([(29, sy + 3), (35, sy + 13), (31, sy + 14), (26.5, sy + 4)], fill=SCARF_LO)
    p.line([(30, sy + 4), (33.5, sy + 12)], width=.8, fill=SCARF)

    # Füße
    for cx, off, lift in ((16, lf, llift), (24, rf, rlift)):
        x0 = cx - 4 + off
        y0 = bot - 2 - lift
        p.ellipse([x0 - .6, y0 - .6, x0 + 8.6, y0 + 4.6], fill=OUT)
        p.ellipse([x0, y0, x0 + 8, y0 + 4], fill=FOOT)
        p.ellipse([x0 + .5, y0 + 2, x0 + 8, y0 + 4], fill=FOOT_LO)
        p.line([(x0 + 2.7, y0 + .5), (x0 + 2.7, y0 + 3)], width=.7, fill=FOOT_LO)
        p.line([(x0 + 5.3, y0 + .5), (x0 + 5.3, y0 + 3)], width=.7, fill=FOOT_LO)

    return p.result()


def gen_pengu():
    frames = [
        draw_pengu(),                                  # idle0
        draw_pengu(blink=True, breathe=1),             # idle1
        draw_pengu(lf=-2, llift=3, rf=2),              # walk0
        draw_pengu(),                                  # walk1
        draw_pengu(lf=2, rf=-2, rlift=3),              # walk2
        draw_pengu(breathe=1),                         # walk3
        draw_pengu(lf=1, rf=-1, llift=3, rlift=3, arms_up=True),  # jump
        draw_pengu(lf=-3, rf=3),                       # fall
        draw_pengu(squash=8),                          # duck
    ]
    _save(_sheet(frames, 40, 48), "characters", "pengu.png")


# =========================================================================
#  Münze (24x24)
# =========================================================================
def gen_coin():
    GOLD = (255, 206, 56, 255)
    GOLD_HI = (255, 244, 190, 255)
    GOLD_LO = (206, 150, 28, 255)
    RIM = (170, 116, 16, 255)
    widths = [22, 16, 9, 3.5, 9, 16]
    frames = []
    for w in widths:
        p = Pen(24, 24)
        cx = 12
        x0, x1 = cx - w / 2, cx + w / 2
        p.ellipse([x0 - 1, 1, x1 + 1, 23], fill=RIM)
        p.ellipse([x0, 2, x1, 22], fill=GOLD_LO)
        p.ellipse([x0 + .8, 2, x1 - .8, 20], fill=GOLD)
        if w >= 8:
            p.ellipse([x0 + 1.5, 4, x1 - 1.5, 13], fill=GOLD_HI)   # oberer Glanz
            p.ellipse([x0 + 3, 6, x1 - 3, 18], outline=GOLD_LO)    # geprägter Ring
            p.line([(cx - 1.5, 6), (cx - 1.5, 11)], width=1, fill=GOLD_HI)
        frames.append(p.result())
    _save(_sheet(frames, 24, 24), "collectibles", "coin.png")


# =========================================================================
#  Gegner „Schneeball" (36x32)
# =========================================================================
def draw_snowball(step: int) -> Image.Image:
    p = Pen(36, 32)
    SNOW = (240, 247, 255, 255)
    SNOW_SH = (198, 214, 236, 255)
    p.ellipse([3, 3, 33, 31], fill=OUT)
    p.ellipse([4, 4, 32, 30], fill=SNOW)
    p.ellipse([6, 14, 30, 29], fill=SNOW_SH)     # unterer Schatten
    p.ellipse([5, 5, 30, 24], fill=SNOW)          # oberer Rundkörper hell
    p.ellipse([9, 7, 18, 14], fill=WHITE)         # Glanz
    # Augen
    for ex in (14, 23):
        p.ellipse([ex - 2.5, 12, ex + 2.5, 19], fill=WHITE, outline=(150, 165, 185, 255))
        p.ellipse([ex - .8, 14, ex + 2, 18.5], fill=PUP)
        p.ellipse([ex, 14.5, ex + 1, 15.8], fill=WHITE)
    # Wangen
    p.ellipse([8, 18, 12, 21], fill=(255, 190, 195, 150))
    p.ellipse([25, 18, 29, 21], fill=(255, 190, 195, 150))
    # Mund
    p.arc([15, 18, 22, 24], 10, 170, width=1.2, fill=PUP)
    # Füße
    fo = 2 if step == 0 else -2
    for cx in (11, 25):
        off = fo if cx == 25 else -fo
        p.ellipse([cx - 4 + off, 28, cx + 4 + off, 32], fill=FOOT)
        p.ellipse([cx - 4 + off, 30, cx + 4 + off, 32], fill=FOOT_LO)
    return p.result()


def draw_snowball_flat() -> Image.Image:
    p = Pen(36, 32)
    SNOW = (240, 247, 255, 255)
    SNOW_SH = (198, 214, 236, 255)
    p.ellipse([2, 22, 34, 31], fill=OUT)
    p.ellipse([3, 23, 33, 30], fill=SNOW)
    p.ellipse([4, 26, 32, 30], fill=SNOW_SH)
    p.line([(12, 26), (15, 26)], width=1.2, fill=PUP)
    p.line([(21, 26), (24, 26)], width=1.2, fill=PUP)
    return p.result()


def gen_snowball():
    frames = [draw_snowball(0), draw_snowball(1), draw_snowball_flat()]
    _save(_sheet(frames, 36, 32), "enemies", "snowball.png")


# =========================================================================
#  Kachelsatz (7 x 32x32)
# =========================================================================
def _pebbles(p, box, colors, seed, count):
    rnd = _lcg(seed)
    x0, y0, x1, y1 = box
    for _ in range(count):
        px = x0 + next(rnd) * (x1 - x0)
        py = y0 + next(rnd) * (y1 - y0)
        r = 0.7 + next(rnd) * 1.6
        c = colors[int(next(rnd) * len(colors)) % len(colors)]
        p.ellipse([px - r, py - r, px + r, py + r], fill=c)


def gen_tileset():
    T = 32
    tiles = []

    # 0: leer
    tiles.append(Image.new("RGBA", (T, T), NONE))

    # 1: Gras-Oberseite
    p = Pen(T, T)
    p.rect([0, 8, T, T], fill=(138, 100, 60, 255))
    _pebbles(p, (0, 10, T, T), [(112, 80, 48, 255), (156, 116, 72, 255)], 11, 60)
    p.rect([0, 0, T, 9], fill=(92, 190, 78, 255))
    p.rect([0, 8, T, 11], fill=(66, 158, 60, 255))
    for x in range(-2, T, 6):
        p.poly([(x, 8), (x + 2, 1), (x + 4, 8)], fill=(112, 214, 96, 255))
    p.line([(0, 2), (T, 2)], width=1, fill=(150, 228, 120, 255))
    tiles.append(p.result())

    # 2: Erde
    p = Pen(T, T)
    p.rect([0, 0, T, T], fill=(138, 100, 60, 255))
    _pebbles(p, (0, 0, T, T), [(112, 80, 48, 255), (160, 120, 76, 255), (98, 70, 42, 255)], 7, 90)
    p.line([(0, 1), (T, 1)], width=1, fill=(160, 120, 76, 255))
    tiles.append(p.result())

    # 3: Ziegel
    p = Pen(T, T)
    p.rect([0, 0, T, T], fill=(120, 60, 44, 255))   # Fuge
    def brick(x0, y0, x1, y1):
        p.rounded([x0, y0, x1, y1], 1.5, fill=(182, 96, 68, 255))
        p.line([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], width=1, fill=(214, 132, 100, 255))
        p.line([(x0 + 1, y1 - 1), (x1 - 1, y1 - 1)], width=1, fill=(150, 74, 52, 255))
    brick(1, 1, 15, 14); brick(17, 1, 31, 14)
    brick(-7, 17, 7, 30); brick(9, 17, 23, 30); brick(25, 17, 39, 30)
    tiles.append(p.result())

    # 4: Hartblock (Metall)
    p = Pen(T, T)
    p.rect([0, 0, T, T], fill=(150, 158, 174, 255))
    p.poly([(0, 0), (T, 0), (T - 4, 4), (4, 4), (4, T - 4), (0, T)], fill=(196, 204, 218, 255))
    p.poly([(T, T), (0, T), (4, T - 4), (T - 4, T - 4), (T - 4, 4), (T, 0)], fill=(104, 112, 130, 255))
    p.rect([5, 5, T - 5, T - 5], fill=(168, 176, 192, 255))
    for cx, cy in ((8, 8), (24, 8), (8, 24), (24, 24)):
        p.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(92, 100, 118, 255))
        p.ellipse([cx - 1.4, cy - 1.4, cx + 1, cy + 1], fill=(198, 206, 220, 255))
    tiles.append(p.result())

    # 5: Stein
    p = Pen(T, T)
    p.rect([0, 0, T, T], fill=(122, 126, 138, 255))
    _pebbles(p, (0, 0, T, T), [(102, 106, 118, 255), (142, 146, 158, 255)], 5, 80)
    p.line([(0, 1), (T, 1)], width=1, fill=(158, 162, 174, 255))
    p.line([(10, 6), (16, 16), (12, 26)], width=1, fill=(96, 100, 112, 255))  # Riss
    tiles.append(p.result())

    # 6: Eis
    p = Pen(T, T)
    p.rect([0, 0, T, T], fill=(178, 226, 246, 255))
    p.poly([(0, 0), (T, 0), (T, 10), (0, 18)], fill=(206, 240, 252, 255))
    p.line([(4, 5), (11, 12)], width=1.4, fill=WHITE)
    p.line([(20, 8), (26, 15)], width=1, fill=(232, 248, 255, 255))
    p.line([(8, 22), (14, 28)], width=1, fill=(150, 206, 232, 255))
    tiles.append(p.result())

    _save(_sheet(tiles, T, T), "tiles", "tileset.png")


# =========================================================================
#  Dekor-Props
# =========================================================================
def gen_props():
    G = (74, 172, 78, 255); GHI = (108, 206, 104, 255); GLO = (52, 138, 62, 255)

    # Busch (48x32)
    p = Pen(48, 32)
    for cx, cy, r in [(13, 22, 11), (25, 16, 13), (36, 22, 10)]:
        p.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1], fill=OUT)
    for cx, cy, r in [(13, 22, 11), (25, 16, 13), (36, 22, 10)]:
        p.ellipse([cx - r, cy - r, cx + r, cy + r], fill=G)
    p.ellipse([18, 8, 33, 20], fill=GHI)
    p.ellipse([10, 26, 40, 34], fill=GLO)
    _save(p.result(), "props", "bush.png")

    # Wolke (96x48)
    p = Pen(96, 48)
    for cx, cy, r in [(26, 32, 16), (46, 22, 22), (68, 30, 17), (44, 36, 20)]:
        p.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 245))
    for cx, cy, r in [(30, 34, 12), (48, 26, 16)]:
        p.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
    p.ellipse([20, 38, 78, 48], fill=(224, 232, 244, 220))
    _save(p.result(), "props", "cloud.png")

    # Baum (64x96)
    p = Pen(64, 96)
    p.rounded([27, 54, 37, 96], 3, fill=(120, 82, 50, 255))
    p.line([(30, 58), (30, 92)], width=1.4, fill=(96, 62, 36, 255))
    p.line([(34, 58), (34, 92)], width=1, fill=(146, 104, 66, 255))
    for cx, cy, r in [(20, 34, 18), (44, 34, 18), (32, 20, 20), (32, 44, 20)]:
        p.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1], fill=OUT)
    for cx, cy, r in [(20, 34, 18), (44, 34, 18), (32, 20, 20), (32, 44, 20)]:
        p.ellipse([cx - r, cy - r, cx + r, cy + r], fill=G)
    p.ellipse([22, 8, 42, 26], fill=GHI)
    p.ellipse([14, 44, 50, 62], fill=GLO)
    _save(p.result(), "props", "tree.png")

    # Zielfahne (32x96)
    p = Pen(32, 96)
    p.rounded([5, 2, 9, 92], 2, fill=(206, 210, 220, 255))
    p.line([(6, 4), (6, 90)], width=1, fill=WHITE)
    p.line([(8.5, 4), (8.5, 90)], width=1, fill=(150, 154, 164, 255))
    p.poly([(9, 4), (30, 12), (9, 22)], fill=(232, 70, 80, 255))
    p.poly([(9, 13), (30, 12), (9, 22)], fill=(196, 48, 60, 255))
    p.line([(9, 5), (27, 11.5)], width=1, fill=(250, 140, 140, 255))
    p.ellipse([2, 88, 22, 96], fill=(120, 90, 60, 255))
    _save(p.result(), "props", "flag.png")


def main():
    print("Erzeuge HD-Pixel-Art ->", IMG)
    gen_tileset()
    gen_pengu()
    gen_coin()
    gen_snowball()
    gen_props()
    print("Fertig.")


if __name__ == "__main__":
    main()
