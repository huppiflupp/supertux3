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


def _c(deg):
    import math
    return math.cos(math.radians(deg))


def _s(deg):
    import math
    return math.sin(math.radians(deg))


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

    # 7: Sand-Oberseite (Wüste)
    p = Pen(T, T)
    p.rect([0, 6, T, T], fill=(214, 176, 110, 255))
    _pebbles(p, (0, 8, T, T), [(198, 158, 92, 255), (228, 194, 132, 255)], 21, 70)
    p.rect([0, 0, T, 7], fill=(238, 208, 138, 255))
    p.line([(0, 1), (T, 1)], width=1, fill=(250, 226, 168, 255))
    for x in range(2, T, 9):        # sanfte Wellenkämme
        p.line([(x, 4), (x + 4, 3), (x + 8, 4)], width=1, fill=(226, 194, 128, 255))
    tiles.append(p.result())

    # 8: Sandstein (Blöcke / Pyramiden)
    p = Pen(T, T)
    p.rect([0, 0, T, T], fill=(198, 162, 104, 255))
    _pebbles(p, (0, 0, T, T), [(182, 146, 90, 255), (214, 180, 122, 255)], 33, 50)
    p.line([(0, 0), (T, 0)], width=1, fill=(226, 196, 138, 255))
    p.line([(0, 16), (T, 16)], width=1, fill=(150, 120, 74, 255))
    p.line([(16, 0), (16, 16)], width=1, fill=(150, 120, 74, 255))
    p.line([(8, 16), (8, T)], width=1, fill=(150, 120, 74, 255))
    p.line([(24, 16), (24, T)], width=1, fill=(150, 120, 74, 255))
    tiles.append(p.result())

    # 9: Mondgestein (Weltraum)
    p = Pen(T, T)
    p.rect([0, 5, T, T], fill=(150, 152, 164, 255))
    _pebbles(p, (0, 6, T, T), [(128, 130, 144, 255), (176, 178, 190, 255)], 41, 70)
    p.rect([0, 0, T, 6], fill=(178, 180, 192, 255))
    for cx, cy, r in [(9, 16, 3), (22, 22, 2.4), (26, 11, 2)]:   # Krater
        p.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(120, 122, 136, 255))
        p.ellipse([cx - r + 1, cy - r + 1, cx + r, cy + r], fill=(160, 162, 176, 255))
    tiles.append(p.result())

    # 10: Metallplatte (Raumstation)
    p = Pen(T, T)
    p.rect([0, 0, T, T], fill=(78, 92, 120, 255))
    p.rect([2, 2, T - 3, T - 3], fill=(96, 112, 146, 255))
    p.line([(0, 16), (T, 16)], width=1, fill=(56, 68, 92, 255))
    p.line([(16, 0), (16, T)], width=1, fill=(56, 68, 92, 255))
    for cx, cy in ((5, 5), (27, 5), (5, 27), (27, 27)):
        p.ellipse([cx - 1.6, cy - 1.6, cx + 1.6, cy + 1.6], fill=(150, 200, 240, 255))
    p.line([(3, 3), (12, 3)], width=1, fill=(140, 170, 210, 255))
    tiles.append(p.result())

    # 11: Asphalt / Straße (Stadt) – Oberkante mit Mittelstreifen
    p = Pen(T, T)
    p.rect([0, 6, T, T], fill=(58, 60, 68, 255))
    _pebbles(p, (0, 8, T, T), [(48, 50, 58, 255), (74, 76, 84, 255)], 61, 80)
    p.rect([0, 0, T, 7], fill=(74, 76, 84, 255))
    p.line([(0, 1), (T, 1)], width=1, fill=(102, 104, 112, 255))
    p.rect([13, 3, 19, 12], fill=(216, 190, 72, 255))     # gelbe Fahrbahnmarkierung
    p.rect([13, 22, 19, 31], fill=(216, 190, 72, 255))
    tiles.append(p.result())

    # 12: Beton / Stahlträger (Baustelle)
    p = Pen(T, T)
    p.rect([0, 0, T, T], fill=(150, 152, 158, 255))       # Beton
    _pebbles(p, (0, 0, T, T), [(134, 136, 142, 255), (170, 172, 178, 255)], 62, 44)
    p.rect([2, 0, 30, 5], fill=(120, 128, 146, 255))      # H-Träger: oberer Flansch
    p.rect([2, 27, 30, 32], fill=(120, 128, 146, 255))    # unterer Flansch
    p.rect([13, 5, 19, 27], fill=(138, 146, 164, 255))    # Steg
    p.line([(13, 5), (13, 27)], width=1, fill=(168, 176, 192, 255))
    for cy in (2, 29):
        for cx in (8, 24):
            p.ellipse([cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5], fill=(92, 98, 112, 255))
            p.ellipse([cx - 1, cy - 1, cx + .6, cy + .6], fill=(176, 184, 200, 255))
    tiles.append(p.result())

    # 13: Schräge steigend-rechts "/"  (Gras über Erde)
    p = Pen(T, T)
    p.poly([(0, T), (T, 0), (T, T)], fill=(138, 100, 60, 255))       # Erde
    p.poly([(0, T), (T, 0), (T, 6), (6, T)], fill=(92, 190, 78, 255))  # Grasband
    p.line([(0, T), (T, 0)], width=1, fill=(120, 214, 96, 255))
    tiles.append(p.result())

    # 14: Schräge steigend-links "\"
    p = Pen(T, T)
    p.poly([(0, 0), (T, T), (0, T)], fill=(138, 100, 60, 255))
    p.poly([(0, 0), (T, T), (T - 6, T), (0, 6)], fill=(92, 190, 78, 255))
    p.line([(0, 0), (T, T)], width=1, fill=(120, 214, 96, 255))
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


# =========================================================================
#  Buddy-System: Schildkröte (Item), Giraffe (Begleiter), Schutzschild
# =========================================================================
def gen_turtle():
    """Schildkröten-Powerup (28x26) – verleiht ein Schutzschild."""
    p = Pen(28, 26)
    SH = (86, 172, 92, 255); SH_LO = (54, 128, 66, 255); SH_HI = (150, 212, 128, 255)
    SKIN = (216, 198, 122, 255); SKIN_LO = (176, 156, 90, 255)
    # Beine
    for cx in (8, 19):
        p.ellipse([cx - 3, 18, cx + 3, 25], fill=OUT)
        p.ellipse([cx - 2.4, 18, cx + 2.4, 24.2], fill=SKIN)
        p.ellipse([cx - 2.4, 21, cx + 2.4, 24.2], fill=SKIN_LO)
    # Kopf (rechts heraus)
    p.ellipse([21, 9, 28, 18], fill=OUT)
    p.ellipse([21.6, 9.6, 27.4, 17.4], fill=SKIN)
    p.ellipse([22, 13, 27, 17.4], fill=SKIN_LO)
    p.ellipse([24, 11.5, 26, 13.8], fill=WHITE)
    p.ellipse([24.4, 12, 25.6, 13.4], fill=PUP)
    # Panzer
    p.ellipse([1, 2, 24, 22], fill=OUT)
    p.ellipse([2, 3, 23, 21], fill=SH)
    p.ellipse([3, 12, 22, 21], fill=SH_LO)
    p.ellipse([4, 4, 20, 14], fill=SH_HI)
    # Hexmuster mittig
    hx, hy, r = 12.5, 12, 5.5
    hexpts = [(hx + r * _c(a), hy + r * _s(a)) for a in (90, 150, 210, 270, 330, 30)]
    p.poly(hexpts, outline=SH_LO)
    for a in range(0, 360, 60):
        x = hx + (r + 3) * _c(a); y = hy + (r + 3) * _s(a)
        p.line([(hx + r * _c(a), hy + r * _s(a)), (x, y)], width=.8, fill=SH_LO)
    _save(p.result(), "collectibles", "turtle.png")


def gen_giraffe():
    """Giraffen-Begleiter (44x60) – legt den Hals als Brücke über Lücken."""
    p = Pen(44, 60)
    Y = (240, 198, 98, 255); Y_LO = (204, 158, 66, 255); Y_HI = (252, 224, 152, 255)
    SPOT = (170, 112, 54, 255); HOOF = (78, 58, 40, 255)
    # Beine
    for lx in (10, 16, 26, 32):
        p.rect([lx - .6, 41, lx + 4.6, 58], fill=OUT)
        p.rect([lx, 42, lx + 4, 58], fill=Y)
        p.rect([lx, 42, lx + 1.8, 58], fill=Y_LO)
        p.rect([lx - .3, 55.5, lx + 4.3, 58], fill=HOOF)
    # Körper
    p.ellipse([7, 29, 39, 49], fill=OUT)
    p.ellipse([8, 30, 38, 48], fill=Y)
    p.ellipse([9, 40, 37, 48], fill=Y_LO)
    p.ellipse([11, 32, 30, 41], fill=Y_HI)
    # Hals nach oben-rechts
    p.poly([(28, 46), (36, 46), (40, 8), (33, 8)], fill=OUT)
    p.poly([(29, 45), (35, 45), (39, 9), (34, 9)], fill=Y)
    p.line([(34.5, 12), (30.5, 44)], width=1.4, fill=Y_LO)
    # Mähne
    p.line([(35, 10), (30, 44)], width=1.8, fill=SPOT)
    # Kopf
    p.ellipse([33, 3, 44, 14], fill=OUT)
    p.ellipse([33.6, 3.6, 43.4, 13.4], fill=Y)
    p.ellipse([39, 8, 44, 13], fill=Y_LO)           # Schnauze
    p.ellipse([40.5, 10, 42.5, 12], fill=SPOT)       # Nüster
    p.ellipse([36.5, 6.5, 39, 9], fill=WHITE)
    p.ellipse([37, 7, 38.6, 8.8], fill=PUP)
    # Ossikone
    p.line([(36, 4), (35, 0.5)], width=1.4, fill=Y_LO)
    p.ellipse([33.6, -0.6, 36.6, 2.4], fill=SPOT)
    # Flecken auf Körper
    for sx, sy in [(13, 34), (20, 37), (28, 39), (16, 41), (24, 33)]:
        p.ellipse([sx, sy, sx + 5, sy + 5], fill=SPOT)
    # kleines Schwänzchen
    p.line([(8, 34), (4, 40)], width=1.4, fill=Y_LO)
    p.ellipse([3, 39, 6, 42], fill=SPOT)
    _save(p.result(), "collectibles", "giraffe.png")


def gen_shield():
    """Schutzschild-Blase (72x72) – wird rotierend um Pengu gezeichnet."""
    p = Pen(72, 72)
    cx = cy = 36
    RING = (120, 232, 184, 235); RING2 = (188, 255, 224, 200)
    DOT = (210, 255, 236, 235)
    # zarte Füllung (Blase)
    p.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(140, 232, 202, 46))
    # Ringe
    p.ellipse([cx - 32, cy - 32, cx + 32, cy + 32], outline=RING, width=3 * SS)
    p.ellipse([cx - 27, cy - 27, cx + 27, cy + 27], outline=RING2, width=2 * SS)
    # rotierende Knoten (zeigen die Drehung)
    for a in range(0, 360, 45):
        x = cx + 32 * _c(a); y = cy + 32 * _s(a)
        p.ellipse([x - 3, y - 3, x + 3, y + 3], fill=DOT)
    # oberer Glanzbogen
    p.arc([cx - 30, cy - 30, cx + 30, cy + 30], 200, 320, width=2, fill=(240, 255, 250, 210))
    _save(p.result(), "collectibles", "shield.png")


# =========================================================================
#  Ägypten-Welt: Hintergrund, Pyramide/Sphinx/Palme/Kaktus, Katzen-Gegner
# =========================================================================
def gen_egypt_bg():
    W, Hh = 1536, 768
    img = Image.new("RGB", (W, Hh))
    d = ImageDraw.Draw(img)
    top, bot = (247, 196, 120), (255, 236, 186)
    for y in range(Hh):
        f = y / (Hh - 1)
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * f) for i in range(3)))
    # Sonne mit weichem Schein
    sx, sy = int(W * 0.70), int(Hh * 0.30)
    for r in range(260, 60, -14):
        t = (260 - r) / 200
        col = tuple(int(255 - 6 * (1 - t)) for _ in range(1)) + (0,)
        c = (min(255, 250 + int(5 * t)), min(255, 226 + int(28 * t)), 150 + int(70 * t))
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=c)
    d.ellipse([sx - 66, sy - 66, sx + 66, sy + 66], fill=(255, 252, 232))
    hor = int(Hh * 0.64)

    def pyramid(cx, wd, ht, col, colhi):
        d.polygon([(cx, hor - ht), (cx - wd, hor), (cx + wd, hor)], fill=col)
        d.polygon([(cx, hor - ht), (cx + wd, hor), (cx + int(wd * 0.12), hor)], fill=colhi)
        for k in range(1, 6):        # Blockreihen
            yy = hor - int(ht * k / 6)
            hw = int(wd * (6 - k) / 6)
            d.line([(cx - hw, yy), (cx + hw, yy)], fill=(170, 138, 84), width=2)
    pyramid(int(W * 0.30), 175, 178, (208, 172, 110), (224, 190, 128))
    pyramid(int(W * 0.44), 128, 128, (198, 162, 100), (214, 180, 118))
    pyramid(int(W * 0.86), 150, 150, (204, 168, 106), (220, 186, 124))
    # Dünen (hinten hell -> vorne dunkler)
    import math as _m
    for li, (cy, col) in enumerate([(hor + 20, (232, 200, 138)),
                                    (hor + 90, (220, 186, 122)),
                                    (hor + 170, (206, 172, 108))]):
        pts = [(0, Hh)]
        for x in range(0, W + 24, 24):
            pts.append((x, cy + int(_m.sin(x * 0.004 + li) * 26)))
        pts.append((W, Hh))
        d.polygon(pts, fill=col)
    (IMG / "background").mkdir(parents=True, exist_ok=True)
    img.save(IMG / "background" / "egypt_desert.png")
    print("  background/egypt_desert.png  (1536, 768)")


def gen_egypt_props():
    SAND = (214, 178, 116, 255); SAND_HI = (232, 200, 140, 255); SAND_LO = (176, 142, 86, 255)
    # Pyramide (96x84)
    p = Pen(96, 84)
    p.poly([(48, 2), (2, 82), (94, 82)], fill=SAND)
    p.poly([(48, 2), (94, 82), (54, 82)], fill=SAND_LO)
    for k in range(1, 7):
        yy = 2 + int(80 * k / 7)
        hw = int(46 * k / 7)
        p.line([(48 - hw, yy), (48 + hw, yy)], width=1, fill=(160, 128, 78, 255))
    p.poly([(48, 2), (44, 14), (52, 14)], fill=SAND_HI)   # Spitzenglanz
    _save(p.result(), "props", "pyramid.png")

    # Sphinx (96x56)
    p = Pen(96, 56)
    p.rounded([6, 30, 84, 54], 5, fill=SAND)              # liegender Körper
    p.rect([70, 30, 90, 54], fill=SAND_LO)
    p.ellipse([70, 8, 94, 40], fill=SAND)                 # Kopf
    p.rect([72, 6, 92, 20], fill=(70, 96, 150, 255))      # Nemes-Kopftuch
    p.rect([72, 6, 92, 10], fill=(210, 180, 60, 255))
    for ex in (78, 88):
        p.ellipse([ex - 2, 22, ex + 2, 26], fill=WHITE)
        p.ellipse([ex - 0.7, 23.3, ex + 0.7, 24.7], fill=PUP)
    p.poly([(6, 30), (2, 52), (12, 52)], fill=SAND_LO)    # Vorderpfoten
    p.line([(20, 40), (60, 40)], width=1, fill=SAND_LO)
    _save(p.result(), "props", "sphinx.png")

    # Palme (56x88)
    p = Pen(56, 88)
    p.rounded([24, 30, 32, 88], 3, fill=(150, 110, 66, 255))
    for yy in range(34, 84, 8):
        p.line([(24, yy), (32, yy)], width=1, fill=(120, 86, 50, 255))
    GRN = (78, 168, 82, 255); GRN_LO = (56, 134, 64, 255)
    for ang, ln in [(-70, 26), (-30, 30), (10, 30), (50, 28), (90, 22), (130, 26)]:
        ex = 28 + ln * _c(ang); ey = 30 + ln * _s(ang) * 0.6 - 6
        p.line([(28, 30), (ex, ey)], width=3, fill=GRN)
        p.ellipse([ex - 4, ey - 3, ex + 4, ey + 3], fill=GRN_LO)
    for cx, cy in ((26, 28), (31, 30), (28, 33)):
        p.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(150, 100, 50, 255))  # Datteln
    _save(p.result(), "props", "palm.png")

    # Kaktus (32x52)
    p = Pen(32, 52)
    CAC = (72, 150, 88, 255); CAC_LO = (52, 120, 70, 255)
    p.rounded([12, 6, 20, 52], 4, fill=CAC)
    p.rounded([4, 20, 12, 34], 4, fill=CAC); p.rounded([4, 20, 12, 24], 3, fill=CAC)
    p.rounded([20, 14, 28, 28], 4, fill=CAC)
    p.line([(16, 8), (16, 50)], width=1, fill=CAC_LO)
    for yy in range(10, 50, 6):
        for sx2 in (11, 21):
            p.ellipse([sx2 - 0.6, yy - 0.6, sx2 + 0.6, yy + 0.6], fill=(230, 240, 200, 255))
    _save(p.result(), "props", "cactus.png")


def draw_cat(step: int) -> Image.Image:
    p = Pen(30, 24)
    GOLD = (226, 176, 92, 255); GOLD_LO = (196, 148, 72, 255); DARK = (60, 44, 30, 255)
    p.ellipse([5, 10, 24, 21], fill=OUT)
    p.ellipse([6, 11, 23, 20], fill=GOLD)                 # Körper
    p.ellipse([7, 15, 22, 20], fill=GOLD_LO)
    # Schwanz (wippt)
    ty = 9 if step == 0 else 12
    p.line([(23, 16), (28, ty)], width=2, fill=GOLD)
    p.ellipse([26, ty - 2, 29, ty + 1], fill=DARK)
    # Kopf
    p.ellipse([2, 6, 13, 17], fill=GOLD)
    p.poly([(3, 8), (2, 1), (7, 6)], fill=GOLD)           # Ohren
    p.poly([(12, 8), (13, 1), (8, 6)], fill=GOLD)
    p.poly([(3.5, 7), (3, 3), (5.5, 6)], fill=(180, 120, 120, 255))
    for ex in (5, 10):
        p.ellipse([ex - 1.5, 9, ex + 1.5, 12], fill=(120, 210, 120, 255))
        p.line([(ex, 9), (ex, 12)], width=.8, fill=PUP)
        p.line([(ex - 2, 8.5), (ex + 2, 8.5)], width=.8, fill=DARK)   # Kajal
    p.poly([(6.5, 12.5), (8.5, 12.5), (7.5, 14)], fill=(200, 120, 110, 255))  # Nase
    # Beine (alternieren)
    fo = 2 if step == 0 else -2
    for cx in (10, 19):
        off = fo if cx == 19 else -fo
        p.rect([cx + off, 20, cx + 2 + off, 24], fill=GOLD_LO)
    return p.result()


def gen_cat():
    _save(_sheet([draw_cat(0), draw_cat(1)], 30, 24), "enemies", "cat.png")


# =========================================================================
#  Weltraum-Welt: Hintergrund, Rakete/Planet/Meteor, Alien-Gegner
# =========================================================================
def gen_space_bg():
    import random as _r
    W, Hh = 1536, 768
    img = Image.new("RGB", (W, Hh))
    d = ImageDraw.Draw(img)
    top, bot = (10, 10, 34), (34, 22, 62)
    for y in range(Hh):
        f = y / (Hh - 1)
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * f) for i in range(3)))
    rng = _r.Random(0x5ACE)
    # Nebel
    for _ in range(5):
        cx, cy = rng.randint(0, W), rng.randint(0, Hh)
        rr = rng.randint(120, 260)
        ov = Image.new("RGBA", (rr * 2, rr * 2), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        col = rng.choice([(90, 60, 160), (40, 80, 160), (150, 60, 130)])
        od.ellipse([0, 0, rr * 2, rr * 2], fill=(*col, 26))
        img.paste(Image.alpha_composite(img.crop((cx - rr, cy - rr, cx + rr, cy + rr)).convert("RGBA"), ov).convert("RGB"),
                  (cx - rr, cy - rr))
    # Sterne
    for _ in range(260):
        x, y = rng.randint(0, W), rng.randint(0, Hh)
        s = rng.choice([1, 1, 1, 2])
        b = rng.randint(160, 255)
        d.ellipse([x, y, x + s, y + s], fill=(b, b, min(255, b + 20)))
    # Großer Ringplanet
    px, py, pr = int(W * 0.22), int(Hh * 0.34), 150
    d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(120, 96, 200))
    d.ellipse([px - pr, py - pr, px + pr, py + pr], outline=(150, 130, 220), width=3)
    d.ellipse([px - pr + 30, py - pr + 24, px + pr - 60, py + pr - 90], fill=(150, 128, 220))
    d.ellipse([px - pr - 60, py - 24, px + pr + 60, py + 40], outline=(200, 180, 240), width=6)  # Ring
    # Kleine ferne Rakete
    rx, ry = int(W * 0.8), int(Hh * 0.5)
    d.polygon([(rx, ry - 40), (rx - 10, ry), (rx + 10, ry)], fill=(220, 90, 90))
    d.polygon([(rx, ry - 40), (rx + 10, ry), (rx + 3, ry)], fill=(180, 70, 74))
    d.ellipse([rx - 4, ry - 26, rx + 4, ry - 18], fill=(150, 210, 240))
    d.polygon([(rx - 6, ry), (rx - 4, ry + 16), (rx + 4, ry + 16), (rx + 6, ry)], fill=(255, 180, 60))
    img.save(IMG / "background" / "space_bg.png")
    print("  background/space_bg.png  (1536, 768)")


def gen_space_props():
    # Rakete (48x96)
    p = Pen(48, 96)
    RED = (222, 78, 80, 255); RED_LO = (172, 50, 56, 255); MET = (208, 214, 226, 255)
    p.ellipse([14, 2, 34, 30], fill=RED)                 # Spitze
    p.rounded([14, 20, 34, 82], 6, fill=MET)             # Rumpf
    p.rounded([16, 22, 26, 80], 4, fill=(232, 238, 248, 255))
    p.ellipse([19, 34, 29, 46], fill=(120, 200, 240, 255))  # Fenster
    p.ellipse([19, 34, 29, 46], outline=(70, 90, 130, 255))
    p.poly([(14, 60), (2, 86), (14, 82)], fill=RED)      # Flossen
    p.poly([(34, 60), (46, 86), (34, 82)], fill=RED_LO)
    p.rounded([16, 80, 32, 88], 3, fill=(90, 100, 120, 255))
    p.poly([(18, 88), (24, 96), (30, 88)], fill=(255, 180, 60, 255))   # Flamme
    _save(p.result(), "props", "rocket.png")

    # Planet (64x64)
    p = Pen(64, 64)
    p.ellipse([6, 8, 58, 60], fill=(96, 150, 210, 255))
    p.ellipse([10, 12, 44, 44], fill=(120, 176, 232, 255))
    p.ellipse([30, 34, 52, 52], fill=(78, 128, 190, 255))
    p.ellipse([1, 26, 63, 42], outline=(220, 210, 160, 255), width=3)  # Ring
    _save(p.result(), "props", "planet.png")

    # Meteor (28x24)
    p = Pen(28, 24)
    p.ellipse([2, 3, 24, 22], fill=(110, 100, 96, 255))
    p.ellipse([3, 4, 23, 20], fill=(140, 130, 122, 255))
    for cx, cy, r in [(9, 9, 2.5), (17, 14, 2), (13, 17, 1.6)]:
        p.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(96, 88, 84, 255))
    _save(p.result(), "props", "meteor.png")


def draw_alien(step: int) -> Image.Image:
    p = Pen(28, 24)
    GRN = (120, 210, 110, 255); GRN_LO = (86, 170, 84, 255)
    # Antenne
    ay = 2 if step == 0 else 4
    p.line([(14, 7), (14, ay)], width=1.4, fill=GRN_LO)
    p.ellipse([12, ay - 2, 16, ay + 2], fill=(255, 120, 120, 255))
    p.ellipse([5, 6, 23, 20], fill=OUT)
    p.ellipse([6, 7, 22, 19], fill=GRN)                   # Kopf/Körper
    p.ellipse([8, 14, 20, 20], fill=GRN_LO)
    p.ellipse([9, 8, 19, 15], fill=WHITE)                 # großes Auge
    p.ellipse([12, 9, 16, 14], fill=PUP)
    p.ellipse([13, 10, 14.5, 11.5], fill=WHITE)
    fo = 2 if step == 0 else -2
    for cx in (10, 18):
        off = fo if cx == 18 else -fo
        p.rect([cx + off, 19, cx + 2 + off, 24], fill=GRN_LO)
    return p.result()


def gen_alien():
    _save(_sheet([draw_alien(0), draw_alien(1)], 28, 24), "enemies", "alien.png")


# =========================================================================
#  Großstadt-Welt: Hintergrund, Wolkenkratzer/Kran/Laterne/Absperrung,
#  Roboter-Gegner
# =========================================================================
def gen_city_bg():
    import random as _r
    W, Hh = 1536, 768
    img = Image.new("RGB", (W, Hh))
    d = ImageDraw.Draw(img)
    # Dämmerungshimmel: violett oben -> warm-orange am Horizont
    top, mid, bot = (26, 24, 62), (96, 62, 116), (238, 146, 96)
    for y in range(Hh):
        f = y / (Hh - 1)
        if f < 0.62:
            g = f / 0.62
            col = tuple(int(top[i] + (mid[i] - top[i]) * g) for i in range(3))
        else:
            g = (f - 0.62) / 0.38
            col = tuple(int(mid[i] + (bot[i] - mid[i]) * g) for i in range(3))
        d.line([(0, y), (W, y)], fill=col)
    # Mond mit weichem Schein
    mx, my = int(W * 0.80), int(Hh * 0.20)
    for r, c in [(104, (66, 54, 100)), (86, (108, 92, 138)), (70, (168, 158, 190)),
                 (56, (240, 238, 246)), (52, (252, 250, 248))]:
        d.ellipse([mx - r, my - r, mx + r, my + r], fill=c)
    for cx, cy, cr in [(mx - 18, my - 10, 9), (mx + 14, my + 10, 6), (mx + 6, my - 20, 5)]:
        d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(224, 220, 232))
    hor = int(Hh * 0.70)

    def skyline(base, col, bw_rng, bh_rng, gap_rng, win, lit_p, seed, jitter=0):
        r2 = _r.Random(seed)
        x = -20
        while x < W + 20:
            bw = r2.randint(*bw_rng)
            bh = r2.randint(*bh_rng)
            top_y = base - bh + r2.randint(-jitter, jitter)
            d.rectangle([x, top_y, x + bw, Hh], fill=col)
            if win is not None:
                for wy in range(top_y + 10, base - 6, 14):
                    for wx in range(x + 7, x + bw - 6, 12):
                        if r2.random() < lit_p:
                            d.rectangle([wx, wy, wx + 6, wy + 8], fill=win)
            x += bw + r2.randint(*gap_rng)

    # ferne Schicht (dunstig, kaum beleuchtet)
    skyline(hor - 40, (58, 52, 92), (70, 130), (120, 240), (14, 40),
            (120, 110, 150), 0.12, 11, jitter=30)
    # mittlere Schicht mit warmen Fensterreihen
    skyline(hor - 6, (40, 38, 66), (56, 110), (150, 300), (10, 30),
            (255, 214, 128), 0.42, 23, jitter=20)
    # Baukran (Silhouette) über der mittleren Schicht
    cxb, ctop = int(W * 0.30), int(Hh * 0.15)
    jy = ctop + 8
    crane = (34, 32, 52)
    lattice = (58, 56, 80)
    d.rectangle([cxb - 6, ctop, cxb + 6, hor], fill=crane)          # Turm
    for yy in range(ctop, hor, 26):
        d.line([(cxb - 6, yy), (cxb + 6, yy + 13)], fill=lattice, width=2)
        d.line([(cxb + 6, yy), (cxb - 6, yy + 13)], fill=lattice, width=2)
    d.polygon([(cxb - 34, jy - 4), (cxb, jy - 52), (cxb + 34, jy - 4)], fill=crane)  # A-Spitze
    d.rectangle([cxb - 110, jy - 7, cxb + 250, jy], fill=crane)     # Ausleger (Jib)
    d.rectangle([cxb - 110, jy - 5, cxb - 84, jy + 10], fill=crane)  # Gegengewicht
    d.rectangle([cxb + 4, jy, cxb + 22, jy + 18], fill=crane)       # Führerkabine
    hx = cxb + 190                                                  # Laufkatze + Seil
    d.line([(hx, jy), (hx, jy + 150)], fill=crane, width=2)
    d.rectangle([hx - 8, jy + 150, hx + 8, jy + 162], fill=crane)   # Haken/Last
    # vordere Schicht (dunkelste Silhouette, dichte Lichter)
    skyline(hor + 30, (24, 22, 40), (60, 130), (120, 260), (6, 22),
            (255, 224, 150), 0.5, 37, jitter=16)
    (IMG / "background").mkdir(parents=True, exist_ok=True)
    img.save(IMG / "background" / "city_bg.png")
    print("  background/city_bg.png  (1536, 768)")


def gen_city_props():
    STEEL = (86, 96, 118, 255); STEEL_LO = (52, 60, 78, 255)
    GLASS = (74, 100, 128, 255); MULL = (120, 150, 176, 255)
    WIN_LIT = (255, 222, 142, 255); WIN_OFF = (52, 78, 100, 255)

    # Wolkenkratzer (72x208) – Glasfassade mit Antenne
    p = Pen(72, 208)
    rnd = _lcg(0xB17)
    p.line([(36, 16), (36, 1)], width=1.6, fill=(70, 76, 92, 255))   # Antenne
    p.ellipse([34, 0, 38, 4], fill=(255, 96, 96, 255))
    p.rect([9, 10, 63, 16], fill=STEEL_LO)                            # Dachkante
    p.rect([5, 16, 67, 208], fill=(44, 52, 70, 255))                 # Rahmen
    p.rect([7, 18, 65, 208], fill=GLASS)                             # Glasfassade
    for wy in range(22, 204, 12):
        for wx in range(11, 60, 11):
            c = WIN_LIT if next(rnd) < 0.45 else WIN_OFF
            p.rect([wx, wy, wx + 7, wy + 8], fill=c)
    for wx in range(10, 66, 11):                                     # vertikale Streben
        p.line([(wx - 1, 18), (wx - 1, 207)], width=1, fill=MULL)
    _save(p.result(), "props", "skyscraper.png")

    # Baukran (140x176) – gelber Turmdrehkran
    p = Pen(140, 176)
    Y = (238, 194, 60, 255); Y_LO = (196, 150, 40, 255); DK = (60, 62, 74, 255)
    tx = 40
    p.rect([tx - 6, 20, tx + 6, 172], fill=Y)                        # Turm
    p.rect([tx - 6, 20, tx - 2, 172], fill=Y_LO)
    for yy in range(24, 168, 18):                                    # Gitterstreben
        p.line([(tx - 6, yy), (tx + 6, yy + 9)], width=1.2, fill=Y_LO)
        p.line([(tx + 6, yy), (tx - 6, yy + 9)], width=1.2, fill=Y_LO)
    p.poly([(tx - 20, 20), (tx, 2), (tx + 20, 20)], fill=Y)          # A-Spitze
    p.line([(tx - 20, 20), (tx, 2)], width=1.4, fill=Y_LO)
    jy = 22
    p.rect([tx - 34, jy - 5, tx + 96, jy + 1], fill=Y)               # Ausleger
    p.rect([tx - 34, jy - 5, tx + 96, jy - 3], fill=Y_LO)
    for jx in range(tx - 30, tx + 92, 12):                           # Fachwerk im Ausleger
        p.line([(jx, jy + 1), (jx + 6, jy - 5)], width=1, fill=Y_LO)
    p.rect([tx - 34, jy - 4, tx - 22, jy + 8], fill=DK)              # Gegengewicht
    p.rect([tx + 2, jy + 1, tx + 16, jy + 16], fill=DK)              # Kabine
    p.rect([tx + 4, jy + 3, tx + 14, jy + 9], fill=(150, 200, 230, 255))
    hx = tx + 74                                                     # Seil + Haken
    p.line([(hx, jy + 1), (hx, jy + 84)], width=1.4, fill=DK)
    p.rect([hx - 5, jy + 84, hx + 5, jy + 92], fill=(70, 72, 84, 255))
    _save(p.result(), "props", "crane.png")

    # Straßenlaterne (28x104)
    p = Pen(28, 104)
    POLE = (70, 74, 88, 255); POLE_HI = (110, 116, 134, 255)
    p.ellipse([6, 99, 22, 104], fill=(50, 54, 66, 255))             # Sockel
    p.rect([12, 14, 16, 102], fill=POLE)
    p.rect([12, 14, 13.4, 102], fill=POLE_HI)
    p.rounded([9, 6, 24, 16], 3, fill=POLE)                         # Ausleger-Kopf
    p.rounded([10, 9, 23, 20], 4, fill=(255, 244, 190, 255))        # Leuchte
    p.ellipse([8, 8, 25, 26], fill=(255, 236, 150, 60))            # Lichtschein
    _save(p.result(), "props", "streetlamp.png")

    # Baustellen-Absperrung / Pylon (34x40)
    p = Pen(34, 40)
    OR = (232, 118, 40, 255); OR_LO = (190, 88, 26, 255)
    p.rect([4, 36, 30, 40], fill=(60, 62, 74, 255))                 # Fußplatte
    p.poly([(17, 4), (7, 36), (27, 36)], fill=OR)                   # Kegel
    p.poly([(17, 4), (27, 36), (20, 36)], fill=OR_LO)               # Schattenseite
    p.poly([(13.5, 15), (20.5, 15), (22.5, 22), (11.5, 22)], fill=(240, 240, 245, 255))  # Reflexband
    p.poly([(11, 27), (23, 27), (25, 33), (9, 33)], fill=(240, 240, 245, 255))
    _save(p.result(), "props", "barrier.png")


def draw_robot(step: int) -> Image.Image:
    p = Pen(30, 30)
    MET = (152, 160, 178, 255); MET_LO = (104, 112, 132, 255)
    MET_HI = (198, 206, 222, 255); EYE = (120, 224, 255, 255)
    # Antenne
    p.line([(15, 8), (15, 3)], width=1.2, fill=MET_LO)
    p.ellipse([13, 1, 17, 5], fill=(255, 96, 96, 255))
    # Blechkörper
    p.rounded([5, 7, 25, 25], 3, fill=OUT)
    p.rounded([6, 8, 24, 24], 3, fill=MET)
    p.rounded([7, 9, 23, 15], 2, fill=MET_HI)                      # Glanz oben
    p.rounded([7, 18, 23, 23], 2, fill=MET_LO)                     # Schatten unten
    # Visier + Auge (wandert -> Blickrichtung wechselt je Frame)
    p.rounded([8, 12, 22, 18], 2, fill=(28, 38, 54, 255))
    ex = 12.5 if step == 0 else 17.5
    p.ellipse([ex - 2.6, 13, ex + 2.6, 17.4], fill=EYE)
    p.ellipse([ex - 1, 13.6, ex + 1.2, 15.6], fill=WHITE)
    # Mund-Gitter
    for gx in range(11, 21, 3):
        p.line([(gx, 20.5), (gx, 22.5)], width=.8, fill=MET_LO)
    # Räder/Füße (alternieren)
    fo = 2 if step == 0 else -2
    for cx in (11, 19):
        off = fo if cx == 19 else -fo
        p.ellipse([cx - 3 + off, 24, cx + 3 + off, 30], fill=MET_LO)
        p.ellipse([cx - 1.6 + off, 25.6, cx + 1.6 + off, 28.6], fill=(38, 42, 54, 255))
    return p.result()


def gen_robot():
    _save(_sheet([draw_robot(0), draw_robot(1)], 30, 30), "enemies", "robot.png")


def gen_friend():
    # kleiner Begleiter-Pinguin (grüner Schal) – wirft Fische auf Gegner
    p = Pen(28, 34)
    GSC = (86, 190, 96, 255); GSC_LO = (56, 150, 70, 255)
    p.ellipse([2, 6, 7, 18], fill=BODY)                 # Flossen
    p.ellipse([21, 6, 26, 18], fill=BODY)
    p.ellipse([3, 2, 25, 32], fill=OUT)
    p.ellipse([4, 3, 24, 31], fill=BODY)
    p.ellipse([7, 4, 17, 13], fill=BODY_HI)
    p.ellipse([8, 12, 21, 30], fill=BELLY)              # Bauch
    for ex in (11, 17):
        p.ellipse([ex - 2, 7, ex + 2, 12], fill=WHITE)
        p.ellipse([ex - .5, 8.5, ex + 1.5, 11.5], fill=PUP)
        p.ellipse([ex, 9, ex + .8, 10], fill=WHITE)
    p.poly([(13, 11), (18, 13), (13, 15)], fill=BEAK)   # Schnabel
    p.rounded([5, 12, 23, 15], 2, fill=GSC)             # grüner Schal
    p.poly([(20, 14), (24, 21), (21, 22), (18, 15)], fill=GSC_LO)
    p.ellipse([9, 31, 14, 34], fill=FOOT); p.ellipse([15, 31, 20, 34], fill=FOOT)
    _save(p.result(), "collectibles", "friend.png")


def main():
    print("Erzeuge HD-Pixel-Art ->", IMG)
    gen_friend()
    gen_egypt_bg()
    gen_egypt_props()
    gen_cat()
    gen_space_bg()
    gen_space_props()
    gen_alien()
    gen_city_bg()
    gen_city_props()
    gen_robot()
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
    gen_turtle()
    gen_giraffe()
    gen_shield()
    gen_props()
    print("Fertig.")


if __name__ == "__main__":
    main()
