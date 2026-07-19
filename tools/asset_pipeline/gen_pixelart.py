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
def _flipper(p, box, top):
    """Zeichnet eine Flosse als gerundete Kontur+Fläche mit Glanz."""
    x0, y0, x1, y1 = box
    p.ellipse([x0 - .8, y0 - .8, x1 + .8, y1 + .8], fill=OUT)
    p.ellipse([x0, y0, x1, y1], fill=BODY)
    p.ellipse([x0 + .5, y0 + 1, x1 - .6, (y0 + y1) / 2], fill=BODY_HI)


def draw_pengu(lf=0.0, rf=0.0, llift=0.0, rlift=0.0, arm="down",
               squash=0.0, blink=False, breathe=0.0) -> Image.Image:
    p = Pen(40, 48)
    top = 5 + squash - breathe
    bot = 46

    # Flossen – Pose bestimmt Haltung (im Ruhezustand hängen sie am Körper)
    t = top
    POSES = {
        "down":  ((3.0, t + 10, 8.0, t + 24), (32.0, t + 10, 37.0, t + 24)),
        "up":    ((0.5, t + 2, 6.0, t + 15), (34.0, t + 2, 39.5, t + 15)),
        "walkA": ((2.0, t + 12, 7.0, t + 25), (33.0, t + 7, 38.0, t + 20)),
        "walkB": ((3.0, t + 7, 8.0, t + 20), (32.0, t + 12, 37.0, t + 25)),
        "fall":  ((0.5, t + 6, 6.0, t + 19), (34.0, t + 6, 39.5, t + 19)),
        "throw": ((3.0, t + 11, 8.0, t + 24), (33.5, t - 3, 40.0, t + 9)),
    }
    lbox, rbox = POSES.get(arm, POSES["down"])
    _flipper(p, lbox, top)
    _flipper(p, rbox, top)

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
    p.ellipse([18, top + 16, 25, top + 30], fill=(255, 255, 255, 255))  # mittiger Glanz

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
    if not blink:
        # Augenbrauen (freundlich)
        p.line([(14.5, ey - 4.5), (19, ey - 3.5)], width=.9, fill=(28, 30, 42, 255))
        p.line([(23, ey - 3.5), (27.5, ey - 4.5)], width=.9, fill=(28, 30, 42, 255))
    # Wangen
    p.ellipse([12.5, ey + 3.5, 16, ey + 6], fill=(255, 150, 160, 120))
    p.ellipse([26, ey + 3.5, 29.5, ey + 6], fill=(255, 150, 160, 120))

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


def _pengu_frames():
    return [
        draw_pengu(arm="down"),                             # idle0
        draw_pengu(arm="down", blink=True, breathe=1),      # idle1
        draw_pengu(lf=-2, llift=3, rf=2, arm="walkA"),      # walk0
        draw_pengu(arm="down"),                             # walk1
        draw_pengu(lf=2, rf=-2, rlift=3, arm="walkB"),      # walk2
        draw_pengu(arm="down", breathe=1),                  # walk3
        draw_pengu(lf=1, rf=-1, llift=3, rlift=3, arm="up"),  # jump
        draw_pengu(lf=-3, rf=3, arm="fall"),                # fall
        draw_pengu(squash=8, arm="down"),                   # duck
        draw_pengu(arm="throw"),                            # throw
    ]


def gen_pengu():
    _save(_sheet(_pengu_frames(), 40, 48), "characters", "pengu.png")


def gen_pengu_big():
    frames = [f.resize((60, 72), Image.LANCZOS) for f in _pengu_frames()]
    _save(_sheet(frames, 60, 72), "characters", "pengu_big.png")


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


# =========================================================================
#  Flieger (40x28, 2 Frames)
# =========================================================================
def draw_flyer(wing_up: bool) -> Image.Image:
    p = Pen(40, 28)
    PURP = (150, 120, 214, 255)
    PURP_LO = (112, 86, 176, 255)
    wy = 6 if wing_up else 14
    for sx, sgn in ((6, -1), (34, 1)):
        p.poly([(20 + sgn * 4, 14), (sx, wy), (sx + sgn * 2, wy + 8)], fill=PURP_LO)
    p.ellipse([11, 7, 29, 25], fill=OUT)
    p.ellipse([12, 8, 28, 24], fill=PURP)
    p.ellipse([13, 9, 25, 17], fill=(180, 156, 232, 255))
    for ex in (17, 23):
        p.ellipse([ex - 2, 13, ex + 2, 18], fill=WHITE, outline=(120, 100, 160, 255))
        p.ellipse([ex - .6, 14.5, ex + 1.6, 17.5], fill=PUP)
    p.arc([17, 18, 23, 22], 10, 170, width=1.1, fill=PUP)
    return p.result()


def gen_flyer():
    _save(_sheet([draw_flyer(True), draw_flyer(False)], 40, 28), "enemies", "flyer.png")


# =========================================================================
#  Stachler (36x34, 2 Frames) – nicht stampfbar
# =========================================================================
def draw_spiky(step: int) -> Image.Image:
    p = Pen(36, 34)
    RED = (206, 78, 54, 255)
    RED_LO = (158, 52, 38, 255)
    # Stacheln oben
    for x in range(6, 32, 5):
        p.poly([(x, 14), (x + 2.5, 2), (x + 5, 14)], fill=(230, 226, 214, 255))
        p.poly([(x + 2.5, 6), (x + 2.5, 2), (x + 5, 14)], fill=(190, 186, 176, 255))
    p.ellipse([5, 10, 31, 31], fill=OUT)
    p.ellipse([6, 11, 30, 30], fill=RED)
    p.ellipse([7, 20, 29, 30], fill=RED_LO)
    p.ellipse([9, 13, 20, 21], fill=(232, 120, 96, 255))
    for ex in (14, 22):
        p.ellipse([ex - 2.4, 17, ex + 2.4, 23], fill=WHITE)
        p.ellipse([ex - .6, 19, ex + 1.8, 22.5], fill=PUP)
    # finstere Brauen
    p.line([(11, 15.5), (16, 17.5)], width=1.1, fill=(40, 20, 16, 255))
    p.line([(25, 15.5), (20, 17.5)], width=1.1, fill=(40, 20, 16, 255))
    p.arc([15, 24, 21, 28], 190, 350, width=1.1, fill=(60, 24, 18, 255))
    fo = 2 if step == 0 else -2
    for cx in (12, 24):
        off = fo if cx == 24 else -fo
        p.ellipse([cx - 4 + off, 29, cx + 4 + off, 34], fill=FOOT)
        p.ellipse([cx - 4 + off, 31, cx + 4 + off, 34], fill=FOOT_LO)
    return p.result()


def gen_spiky():
    _save(_sheet([draw_spiky(0), draw_spiky(1)], 36, 34), "enemies", "spiky.png")


# =========================================================================
#  Sprungfeder (32x24, 2 Frames)
# =========================================================================
def draw_spring(compressed: bool) -> Image.Image:
    p = Pen(32, 24)
    top = 12 if compressed else 4
    MET = (200, 60, 70, 255)
    MET_HI = (240, 130, 140, 255)
    p.rounded([3, 21, 29, 24], 1.5, fill=(90, 94, 104, 255))       # Basis
    # Spirale
    for i in range(3):
        y = top + 3 + i * ((20 - top) / 3)
        p.rounded([5, y, 27, y + 2.5], 2, fill=MET, outline=(150, 40, 50, 255))
    p.rounded([2, top, 30, top + 5], 2, fill=(150, 156, 168, 255))  # Platte
    p.rounded([3, top + 1, 29, top + 2.5], 2, fill=(210, 216, 228, 255))
    return p.result()


def gen_spring():
    _save(_sheet([draw_spring(False), draw_spring(True)], 32, 24), "props", "spring.png")


# =========================================================================
#  Checkpoint (32x64, 2 Frames: aus / an)
# =========================================================================
def draw_checkpoint(active: bool) -> Image.Image:
    p = Pen(32, 64)
    p.rounded([6, 2, 10, 60], 2, fill=(150, 154, 164, 255))
    p.line([(7.5, 4), (7.5, 58)], width=1, fill=(210, 214, 224, 255))
    p.ellipse([3, 58, 20, 64], fill=(120, 124, 134, 255))
    if active:
        p.poly([(10, 6), (30, 12), (10, 20)], fill=(90, 210, 110, 255))
        p.poly([(10, 13), (30, 12), (10, 20)], fill=(60, 176, 84, 255))
        p.ellipse([5, 4, 12, 11], fill=(160, 255, 180, 200))   # Leuchten
    else:
        p.poly([(10, 30), (24, 34), (10, 42)], fill=(150, 156, 168, 255))
        p.poly([(10, 36), (24, 34), (10, 42)], fill=(120, 126, 138, 255))
    return p.result()


def gen_checkpoint():
    _save(_sheet([draw_checkpoint(False), draw_checkpoint(True)], 32, 64), "props", "checkpoint.png")


# =========================================================================
#  Wachstums-Item (28x28) – leuchtendes Ei
# =========================================================================
def gen_grow():
    p = Pen(28, 28)
    p.ellipse([4, 2, 24, 26], fill=OUT)
    p.ellipse([5, 3, 23, 25], fill=(255, 244, 214, 255))
    p.ellipse([6, 4, 20, 16], fill=WHITE)
    for cx, cy, r in [(9, 17, 2.4), (16, 20, 2), (18, 11, 1.8), (12, 12, 1.6)]:
        p.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 176, 60, 255))
    # kleiner Stern
    p.poly([(14, 6), (15.4, 9.4), (18.8, 9.4), (16, 11.6),
            (17, 15), (14, 13), (11, 15), (12, 11.6),
            (9.2, 9.4), (12.6, 9.4)], fill=(255, 120, 90, 255))
    _save(p.result(), "collectibles", "grow.png")


# =========================================================================
#  Boss „Frostkönig" (64x60, 3 Frames: walk0, walk1, hurt)
# =========================================================================
def draw_boss(step: int, hurt: bool = False) -> Image.Image:
    p = Pen(64, 60)
    SNOW = (238, 246, 255, 255)
    SNOW_SH = (196, 214, 238, 255)
    GOLD = (255, 208, 60, 255)
    GOLD_LO = (206, 150, 30, 255)
    # Körper
    p.ellipse([7, 15, 57, 59], fill=OUT)
    p.ellipse([8, 16, 56, 58], fill=SNOW)
    p.ellipse([12, 34, 52, 57], fill=SNOW_SH)
    p.ellipse([10, 17, 48, 40], fill=SNOW)
    p.ellipse([16, 20, 34, 33], fill=WHITE)
    # Krone
    p.rect([20, 12, 44, 17], fill=GOLD)
    for cx in (20, 32, 44):
        p.poly([(cx - 4, 13), (cx, 3), (cx + 4, 13)], fill=GOLD)
        p.ellipse([cx - 2, 1, cx + 2, 5], fill=(255, 240, 160, 255))
    p.line([(21, 16), (43, 16)], width=1, fill=GOLD_LO)
    # Arme
    p.ellipse([2, 34, 12, 46], fill=SNOW); p.ellipse([2, 34, 12, 46], outline=SNOW_SH)
    p.ellipse([52, 34, 62, 46], fill=SNOW); p.ellipse([52, 34, 62, 46], outline=SNOW_SH)
    # Gesicht
    if hurt:
        for ex in (25, 39):
            p.line([(ex - 3, 26), (ex + 3, 32)], width=1.3, fill=PUP)
            p.line([(ex + 3, 26), (ex - 3, 32)], width=1.3, fill=PUP)
        p.ellipse([28, 36, 36, 44], fill=PUP)   # offener Mund
    else:
        for ex in (25, 39):
            p.ellipse([ex - 3.5, 25, ex + 3.5, 33], fill=WHITE, outline=(150, 165, 185, 255))
            p.ellipse([ex - 1, 27, ex + 2.5, 32], fill=PUP)
            p.ellipse([ex, 27.5, ex + 1.2, 29], fill=WHITE)
        p.line([(20, 22), (30, 25)], width=1.4, fill=(40, 50, 70, 255))   # Brauen
        p.line([(44, 22), (34, 25)], width=1.4, fill=(40, 50, 70, 255))
        p.arc([26, 38, 38, 46], 190, 350, width=1.4, fill=PUP)            # finster
    # Füße
    fo = 3 if step == 0 else -3
    for cx in (22, 42):
        off = fo if cx == 42 else -fo
        p.ellipse([cx - 6 + off, 55, cx + 6 + off, 60], fill=FOOT)
        p.ellipse([cx - 6 + off, 57, cx + 6 + off, 60], fill=FOOT_LO)
    return p.result()


def gen_boss():
    _save(_sheet([draw_boss(0), draw_boss(1), draw_boss(0, hurt=True)], 64, 60),
          "enemies", "boss.png")


def gen_iceball():
    p = Pen(16, 16)
    p.ellipse([1, 1, 15, 15], fill=(120, 190, 230, 255))
    p.ellipse([2, 2, 14, 14], fill=(176, 224, 246, 255))
    p.poly([(8, 2), (10, 8), (8, 14), (6, 8)], fill=(210, 240, 252, 255))
    p.line([(4, 5), (8, 9)], width=1, fill=WHITE)
    _save(p.result(), "enemies", "iceball.png")


def gen_star():
    import math as _m
    p = Pen(24, 24)
    cx, cy, R, r = 12, 12.5, 11, 4.6
    pts = []
    for i in range(10):
        ang = -_m.pi / 2 + i * _m.pi / 5
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad * _m.cos(ang), cy + rad * _m.sin(ang)))
    # Kontur + Füllung
    op = [(cx + (x - cx) * 1.12, cy + (y - cy) * 1.12) for x, y in pts]
    p.poly(op, fill=OUT)
    p.poly(pts, fill=(255, 214, 70, 255))
    inner = [(cx + (x - cx) * 0.55, cy + (y - cy) * 0.55) for x, y in pts]
    p.poly(inner, fill=(255, 244, 180, 255))
    p.ellipse([8, 6, 12, 10], fill=WHITE)
    _save(p.result(), "collectibles", "star.png")


# =========================================================================
#  HUD-Icons, Fisch, Schützen-Pflanze, Loot-Box, Flugzeug, Feuerball
# =========================================================================
def gen_hud_icons():
    # Herz (Leben)
    p = Pen(16, 16)
    RED = (232, 72, 84, 255); RED_HI = (255, 140, 150, 255)
    p.ellipse([2, 3, 8, 9], fill=RED); p.ellipse([8, 3, 14, 9], fill=RED)
    p.poly([(2.5, 7), (13.5, 7), (8, 14)], fill=RED)
    p.ellipse([4, 4, 7, 7], fill=RED_HI)
    _save(p.result(), "ui", "heart.png")
    # Uhr (Zeit)
    p = Pen(16, 16)
    p.ellipse([1, 1, 15, 15], fill=(60, 66, 84, 255))
    p.ellipse([2, 2, 14, 14], fill=(232, 238, 248, 255))
    p.ellipse([2, 2, 14, 14], outline=(120, 128, 146, 255))
    p.line([(8, 8), (8, 4)], width=1.4, fill=(40, 46, 62, 255))
    p.line([(8, 8), (11, 9)], width=1.4, fill=(40, 46, 62, 255))
    _save(p.result(), "ui", "clock.png")


def gen_fish():
    p = Pen(20, 14)
    BLU = (96, 176, 224, 255); BLU_LO = (60, 130, 180, 255); BLU_HI = (170, 220, 245, 255)
    p.ellipse([1, 2, 15, 12], fill=OUT)
    p.ellipse([2, 3, 15, 11], fill=BLU)
    p.ellipse([3, 3.5, 12, 7.5], fill=BLU_HI)
    p.ellipse([6, 6, 14, 11], fill=BLU_LO)
    p.poly([(14, 7), (20, 2), (20, 12)], fill=BLU)         # Schwanz
    p.poly([(15, 7), (19, 4), (19, 10)], fill=BLU_LO)
    p.ellipse([4, 5, 6.5, 7.5], fill=WHITE)                # Auge
    p.ellipse([4.6, 5.6, 6, 7], fill=PUP)
    _save(p.result(), "collectibles", "fish.png")


def draw_plant(open_mouth: bool) -> Image.Image:
    p = Pen(28, 28)
    GREEN = (74, 168, 78, 255); GREEN_LO = (52, 130, 60, 255)
    RED = (222, 74, 70, 255); RED_LO = (170, 44, 44, 255)
    # Stiel + Blätter
    p.rect([12, 16, 16, 28], fill=GREEN)
    p.line([(14, 18), (14, 27)], width=1, fill=GREEN_LO)
    p.ellipse([4, 18, 13, 24], fill=GREEN); p.ellipse([15, 18, 24, 24], fill=GREEN_LO)
    # Kopf
    p.ellipse([5, 3, 23, 19], fill=OUT)
    p.ellipse([6, 4, 22, 18], fill=RED)
    p.ellipse([8, 5, 18, 12], fill=(240, 120, 110, 255))
    if open_mouth:
        p.poly([(9, 11), (19, 11), (14, 17)], fill=(60, 20, 20, 255))   # offener Schlund
        for x in (10, 13, 16):
            p.poly([(x, 11), (x + 1.5, 13.5), (x + 3, 11)], fill=WHITE)  # Zähne
    else:
        p.line([(9, 12), (19, 12)], width=1.2, fill=RED_LO)
    for ex in (10, 18):
        p.ellipse([ex - 2, 6, ex + 2, 10], fill=WHITE)
        p.ellipse([ex - .6, 7, ex + 1.4, 9.5], fill=PUP)
    _save_none = None
    return p.result()


def gen_plant():
    _save(_sheet([draw_plant(False), draw_plant(True)], 28, 28), "enemies", "plant.png")


def gen_box():
    p = Pen(32, 32)
    G = (240, 190, 60, 255); G_LO = (196, 146, 30, 255); G_HI = (255, 224, 130, 255)
    p.rounded([1, 1, 31, 31], 3, fill=G_LO)
    p.rounded([2, 2, 30, 30], 3, fill=G)
    p.rounded([3, 3, 29, 12], 2, fill=G_HI)
    for cx, cy in ((5, 5), (27, 5), (5, 27), (27, 27)):
        p.ellipse([cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5], fill=G_LO)
    # Fragezeichen
    p.arc([11, 8, 21, 18], 20, 300, width=3, fill=(120, 80, 10, 255))
    p.line([(16, 16), (16, 20)], width=3, fill=(120, 80, 10, 255))
    p.ellipse([14.5, 22, 17.5, 25], fill=(120, 80, 10, 255))
    _save(p.result(), "props", "box.png")


def gen_plane():
    p = Pen(56, 28)
    RED = (216, 76, 78, 255); RED_LO = (168, 48, 52, 255)
    p.ellipse([6, 10, 46, 22], fill=OUT)
    p.ellipse([7, 11, 45, 21], fill=RED)                 # Rumpf
    p.ellipse([8, 12, 30, 17], fill=(240, 130, 130, 255))
    p.poly([(20, 16), (34, 4), (40, 6), (30, 16)], fill=(230, 210, 120, 255))  # Flügel
    p.poly([(6, 12), (0, 8), (2, 16)], fill=RED_LO)      # Heck
    # Cockpit + Pilot (kleiner Pinguin)
    p.ellipse([30, 6, 42, 16], fill=(180, 220, 245, 200))
    p.ellipse([32, 7, 40, 15], fill=BODY)
    p.ellipse([33, 9, 37, 13], fill=BELLY)
    # Propeller
    p.line([(46, 10), (46, 22)], width=2, fill=(60, 66, 84, 255))
    p.ellipse([44, 14, 48, 18], fill=(40, 44, 60, 255))
    _save(p.result(), "props", "plane.png")


def gen_fireball():
    p = Pen(14, 14)
    p.ellipse([1, 1, 13, 13], fill=(230, 120, 30, 255))
    p.ellipse([2, 2, 12, 12], fill=(255, 176, 46, 255))
    p.ellipse([3, 3, 9, 9], fill=(255, 232, 140, 255))
    _save(p.result(), "enemies", "fireball.png")


def main():
    print("Erzeuge HD-Pixel-Art ->", IMG)
    gen_tileset()
    gen_pengu()
    gen_pengu_big()
    gen_coin()
    gen_snowball()
    gen_flyer()
    gen_spiky()
    gen_boss()
    gen_iceball()
    gen_spring()
    gen_checkpoint()
    gen_grow()
    gen_star()
    gen_hud_icons()
    gen_fish()
    gen_plant()
    gen_box()
    gen_plane()
    gen_fireball()
    gen_props()
    print("Fertig.")


if __name__ == "__main__":
    main()
