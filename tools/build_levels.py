#!/usr/bin/env python3
"""Baut levels/level1..6.json deterministisch auf.

Boden: Reihe 15 (Gras) / 16 (Erde). Etwas 'auf dem Boden' -> ty=14.
Sprunghöhe ~3.7 Kacheln, Weite ~5 Kacheln -> Abgründe <=4 Kacheln sind fair;
größere Lücken werden mit beweglichen Plattformen überbrückt.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
H = 17
GROUND = 15
FLOOR = 14


class B:
    def __init__(self, w):
        self.w = w
        self.g = [["." for _ in range(w)] for _ in range(H)]
        self.ent = []
        self.props = []

    def put(self, x, y, ch):
        if 0 <= y < H and 0 <= x < self.w:
            self.g[y][x] = ch

    def ground(self, x0, x1, ch="G", fill="D"):
        for x in range(x0, x1 + 1):
            self.put(x, GROUND, ch)
            self.put(x, GROUND + 1, fill)

    def plat(self, x0, x1, y, ch="B"):
        for x in range(x0, x1 + 1):
            self.put(x, y, ch)

    def stair(self, x0, height, ch="D", top="G"):
        for i in range(height):
            for y in range(GROUND - i, GROUND + 2):
                self.put(x0 + i, y, ch)
            self.put(x0 + i, GROUND - i, top)

    def wall(self, x, y0, y1, ch="S"):
        for y in range(y0, y1 + 1):
            self.put(x, y, ch)

    def coins(self, x0, x1, y):
        for x in range(x0, x1 + 1):
            self.ent.append(["coin", x, y])

    def arc(self, cx, y):
        self.ent += [["coin", cx - 1, y], ["coin", cx, y - 1], ["coin", cx + 1, y]]

    def e(self, *a):
        self.ent.append(list(a))

    def prop(self, name, x, y=FLOOR):
        self.props.append([name, x, y])

    def surface_row(self, x):
        for y in range(H):
            if self.g[y][x] in "GDBSI#":
                return y
        return None

    def sprinkle_stars(self, n=3):
        for i in range(n):
            x0 = int(self.w * (i + 1) / (n + 1))
            for dx in range(0, 10):
                placed = False
                for xx in (x0 + dx, x0 - dx):
                    if 0 <= xx < self.w:
                        sy = self.surface_row(xx)
                        if sy is not None and sy >= 4:
                            self.e("star", xx, sy - 3)
                            placed = True
                            break
                if placed:
                    break

    def dump(self, path, name, theme, spawn=(2, FLOOR), bg=None, music=None):
        if not any(e[0] == "star" for e in self.ent) and \
                not any(e[0] == "boss" for e in self.ent):
            self.sprinkle_stars()
        data = {"name": name, "theme": theme, "spawn": list(spawn),
                "solid": ["".join(r) for r in self.g],
                "props": self.props, "entities": self.ent}
        if bg:
            data["background"] = bg
        if music:
            data["music"] = music
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0)
        print(f"  {path.name}: {name} ({self.w}x{H}, {len(self.ent)} ent, {len(self.props)} props)")


LV = ROOT / "levels"
LV.mkdir(exist_ok=True)


# --- Level 1: sanfter Einstieg ------------------------------------------
def level1():
    b = B(150)
    pits = [(31, 34), (63, 66), (98, 101)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1); x = c + 1
    b.ground(x, 149)
    for x0, x1, y in [(18, 22, 11), (26, 28, 9), (44, 49, 10), (72, 77, 11), (110, 114, 10)]:
        b.plat(x0, x1, y)
    b.stair(128, 4); b.plat(132, 149, GROUND - 4)
    b.coins(6, 9, 12); b.arc(32, 12); b.coins(19, 21, 9); b.arc(64, 12)
    b.coins(45, 48, 8); b.arc(99, 12); b.coins(72, 76, 9); b.coins(133, 138, GROUND - 5)
    b.e("growth", 27, 8); b.e("spring", 88, FLOOR)
    for ex in (14, 40, 58, 82, 106, 138):
        b.e("snowball", ex, FLOOR)
    b.e("fish", 12, 12)                       # Fisch-Wurf-Powerup
    b.e("turtle", 8, 12)                       # Schildkröte -> Schutzschild
    b.e("giraffe", 55, 11)                     # Giraffe -> Brücke über Pit 63-66
    b.e("box", 24, 11); b.e("box", 25, 11)    # zerstörbare Loot-Boxen
    b.e("shooter", 52, FLOOR)                 # schießende Pflanze
    b.e("fishrain", 118, 9)                   # Fischregen-Powerup
    b.e("checkpoint", 70, FLOOR); b.e("goal", 146, GROUND - 4)
    for t in (5, 24, 52, 90, 125):
        b.prop("bush", t)
    for t in (10, 48, 108):
        b.prop("tree", t)
    for t, y in [(12, 2), (30, 1), (75, 2), (120, 2)]:
        b.prop("cloud", t, y)
    b.dump(LV / "level1.json", "Grüne Hügel 1", "grass")


# --- Level 2: Federn & Plattformen (Sonnenuntergang) --------------------
def level2():
    b = B(160)
    pits = [(24, 28), (46, 52), (74, 79), (104, 110), (132, 137)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1); x = c + 1
    b.ground(x, 159)
    b.e("mplat", 46, 11, 52, 11, 3); b.e("mplat", 104, 12, 110, 8, 3)
    b.plat(60, 64, 9); b.plat(86, 90, 10); b.plat(118, 122, 9)
    b.e("spring", 22, FLOOR); b.e("spring", 72, FLOOR); b.e("spring", 130, FLOOR)
    b.arc(26, 8); b.arc(49, 9); b.arc(76, 8); b.arc(107, 10); b.arc(134, 8)
    b.coins(60, 64, 8); b.coins(86, 90, 9); b.coins(118, 122, 8)
    b.e("growth", 62, 8)
    for ex in (16, 40, 66, 96, 124, 150):
        b.e("snowball", ex, FLOOR)
    b.e("flyer", 55, 8, 5); b.e("flyer", 115, 7, 5)
    b.e("checkpoint", 80, FLOOR); b.e("goal", 156, FLOOR)
    for t in (8, 35, 92, 145):
        b.prop("bush", t)
    for t in (18, 100):
        b.prop("tree", t)
    b.dump(LV / "level2.json", "Sonnige Hänge", "sunset")


# --- Level 3: Wolkensprung – viele bewegliche Plattformen ---------------
def level3():
    b = B(170)
    b.ground(0, 12)
    b.ground(20, 30); b.ground(40, 52); b.ground(70, 84)
    b.ground(104, 120); b.ground(150, 169)
    b.e("mplat", 13, 12, 19, 12, 3)
    b.e("mplat", 31, 12, 39, 9, 3)
    b.e("mplat", 53, 11, 69, 11, 3)
    b.e("mplat", 85, 10, 103, 13, 3)
    b.e("mplat", 121, 12, 149, 12, 4)
    for cx in (16, 35, 60, 94, 135):
        b.arc(cx, 9)
    b.coins(22, 28, 12); b.coins(42, 50, 12); b.coins(72, 82, 12); b.coins(106, 118, 12)
    b.e("growth", 46, 12)
    for ex in (24, 46, 76, 110, 158):
        b.e("snowball", ex, FLOOR)
    b.e("flyer", 35, 7, 6); b.e("flyer", 90, 6, 8); b.e("flyer", 135, 8, 6)
    b.e("spring", 10, FLOOR); b.e("spring", 160, FLOOR)
    b.e("checkpoint", 78, FLOOR); b.e("goal", 166, FLOOR)
    for t, y in [(10, 1), (44, 2), (90, 1), (130, 2)]:
        b.prop("cloud", t, y)
    b.dump(LV / "level3.json", "Wolkensprung", "grass")


# --- Level 4: Eishöhle – Stachler & Eis ---------------------------------
def level4():
    b = B(160)
    pits = [(30, 34), (58, 62), (92, 97), (124, 129)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1, ch="I", fill="I"); x = c + 1
    b.ground(x, 159, ch="I", fill="I")
    for x0, x1, y in [(18, 24, 11), (44, 50, 10), (74, 80, 11), (108, 114, 10)]:
        b.plat(x0, x1, y, "I")
    b.e("mplat", 58, 12, 62, 12, 3); b.e("mplat", 124, 11, 129, 11, 3)
    b.arc(32, 12); b.arc(60, 12); b.arc(94, 12); b.arc(126, 12)
    b.coins(18, 24, 9); b.coins(74, 80, 9); b.coins(108, 114, 8)
    b.e("growth", 46, 8)
    for ex in (16, 46, 78, 112, 148):
        b.e("spiky", ex, FLOOR)
    for ex in (40, 100):
        b.e("snowball", ex, FLOOR)
    b.e("spring", 88, FLOOR)
    b.e("checkpoint", 70, FLOOR); b.e("goal", 156, FLOOR)
    b.dump(LV / "level4.json", "Eishöhle", "ice")


# --- Level 5: Nacht am Hügel – Mix --------------------------------------
def level5():
    b = B(165)
    pits = [(26, 30), (52, 57), (84, 89), (116, 121), (140, 145)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1); x = c + 1
    b.ground(x, 164)
    for x0, x1, y in [(20, 24, 10), (64, 70, 9), (98, 104, 10), (128, 134, 9)]:
        b.plat(x0, x1, y)
    b.e("mplat", 52, 11, 57, 8, 3); b.e("mplat", 116, 12, 121, 12, 3)
    b.e("spring", 24, FLOOR); b.e("spring", 82, FLOOR); b.e("spring", 138, FLOOR)
    b.arc(28, 8); b.arc(54, 9); b.arc(86, 8); b.arc(118, 9); b.arc(142, 8)
    b.coins(64, 70, 8); b.coins(98, 104, 9); b.coins(128, 134, 8)
    b.e("growth", 66, 7)
    for ex in (16, 44, 74, 108, 150):
        b.e("snowball", ex, FLOOR)
    for ex in (38, 96, 132):
        b.e("spiky", ex, FLOOR)
    b.e("flyer", 60, 7, 6); b.e("flyer", 124, 6, 7)
    b.e("checkpoint", 90, FLOOR); b.e("goal", 161, FLOOR)
    for t in (12, 100):
        b.prop("tree", t)
    for t, y in [(20, 2), (70, 1), (130, 2)]:
        b.prop("cloud", t, y)
    b.dump(LV / "level5.json", "Nacht am Hügel", "night")


# --- Level 6: Kristallhöhle – Finale ------------------------------------
def level6():
    b = B(185)
    pits = [(22, 26), (40, 45), (62, 68), (88, 94), (112, 118), (140, 146), (160, 165)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1, ch="S", fill="S"); x = c + 1
    b.ground(x, 184, ch="S", fill="S")
    for x0, x1, y in [(32, 36, 10), (74, 80, 9), (100, 106, 11), (128, 134, 9)]:
        b.plat(x0, x1, y, "S")
    b.e("mplat", 40, 12, 45, 9, 3)
    b.e("mplat", 62, 11, 68, 11, 3)
    b.e("mplat", 112, 10, 118, 13, 3)
    b.e("mplat", 160, 12, 165, 12, 4)
    b.e("spring", 20, FLOOR); b.e("spring", 86, FLOOR); b.e("spring", 138, FLOOR)
    for cx in (24, 42, 64, 90, 114, 142, 162):
        b.arc(cx, 9)
    b.coins(74, 80, 8); b.coins(100, 106, 10); b.coins(128, 134, 8)
    b.e("growth", 34, 8); b.e("growth", 130, 7)
    for ex in (16, 52, 96, 150, 178):
        b.e("snowball", ex, FLOOR)
    for ex in (34, 78, 104, 132, 172):
        b.e("spiky", ex, FLOOR)
    b.e("flyer", 48, 7, 6); b.e("flyer", 108, 6, 7); b.e("flyer", 156, 7, 6)
    b.e("checkpoint", 70, FLOOR); b.e("checkpoint", 130, FLOOR)
    b.e("goal", 181, FLOOR)
    b.dump(LV / "level6.json", "Kristallhöhle", "cave")


# --- Level 7: Frostwind-Grat (Eis) --------------------------------------
def level7():
    b = B(170)
    pits = [(28, 32), (54, 60), (86, 91), (118, 124), (146, 151)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1, ch="I", fill="I"); x = c + 1
    b.ground(x, 169, ch="I", fill="I")
    for x0, x1, y in [(20, 26, 10), (66, 72, 9), (100, 106, 10), (132, 138, 9)]:
        b.plat(x0, x1, y, "I")
    b.e("mplat", 54, 11, 60, 8, 3); b.e("mplat", 118, 12, 124, 12, 3)
    b.e("spring", 26, FLOOR); b.e("spring", 84, FLOOR); b.e("spring", 144, FLOOR)
    b.arc(30, 8); b.arc(57, 9); b.arc(88, 8); b.arc(121, 9); b.arc(148, 8)
    b.coins(66, 72, 8); b.coins(100, 106, 9); b.coins(132, 138, 8)
    b.e("growth", 68, 7)
    for ex in (18, 46, 78, 110, 158):
        b.e("spiky", ex, FLOOR)
    for ex in (40, 96):
        b.e("snowball", ex, FLOOR)
    b.e("flyer", 62, 7, 6); b.e("flyer", 128, 6, 7)
    b.e("checkpoint", 92, FLOOR); b.e("goal", 166, FLOOR)
    b.dump(LV / "level7.json", "Frostwind-Grat", "ice")


# --- Level 8: Tiefe Stollen (Höhle) -------------------------------------
def level8():
    b = B(175)
    pits = [(24, 29), (48, 54), (78, 84), (108, 114), (138, 143), (158, 163)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1, ch="S", fill="S"); x = c + 1
    b.ground(x, 174, ch="S", fill="S")
    for x0, x1, y in [(34, 40, 10), (66, 72, 9), (96, 102, 11), (126, 132, 9)]:
        b.plat(x0, x1, y, "S")
    b.e("mplat", 48, 12, 54, 9, 3); b.e("mplat", 108, 11, 114, 11, 3)
    b.e("spring", 22, FLOOR); b.e("spring", 76, FLOOR); b.e("spring", 136, FLOOR)
    for cx in (26, 50, 80, 110, 140):
        b.arc(cx, 9)
    b.coins(66, 72, 8); b.coins(96, 102, 10); b.coins(126, 132, 8)
    b.e("growth", 36, 8)
    for ex in (16, 44, 90, 150, 170):
        b.e("spiky", ex, FLOOR)
    for ex in (60, 120):
        b.e("snowball", ex, FLOOR)
    b.e("flyer", 70, 7, 6); b.e("flyer", 130, 6, 7)
    b.e("checkpoint", 86, FLOOR); b.e("goal", 171, FLOOR)
    b.dump(LV / "level8.json", "Tiefe Stollen", "cave")


# --- Level 9: Sternenhimmel (Nacht) -------------------------------------
def level9():
    b = B(175)
    b.ground(0, 14)
    b.ground(22, 34); b.ground(44, 58); b.ground(76, 92)
    b.ground(112, 128); b.ground(156, 174)
    b.e("mplat", 15, 12, 21, 12, 3)
    b.e("mplat", 35, 12, 43, 9, 3)
    b.e("mplat", 59, 11, 75, 11, 3)
    b.e("mplat", 93, 10, 111, 13, 3)
    b.e("mplat", 129, 12, 155, 12, 4)
    for cx in (18, 39, 66, 102, 142):
        b.arc(cx, 9)
    b.coins(24, 32, 12); b.coins(46, 56, 12); b.coins(78, 90, 12); b.coins(114, 126, 12)
    b.e("growth", 50, 12)
    for ex in (26, 50, 82, 118, 164):
        b.e("snowball", ex, FLOOR)
    for ex in (30, 86, 122):
        b.e("spiky", ex, FLOOR)
    b.e("flyer", 40, 7, 6); b.e("flyer", 96, 6, 8); b.e("flyer", 140, 8, 6)
    b.e("spring", 12, FLOOR); b.e("spring", 166, FLOOR)
    b.e("checkpoint", 84, FLOOR); b.e("goal", 171, FLOOR)
    for t, y in [(10, 1), (48, 2), (96, 1), (140, 2)]:
        b.prop("cloud", t, y)
    b.dump(LV / "level9.json", "Sternenhimmel", "night")


# --- Level 10: Frostkönigs Festung (Boss) -------------------------------
def level10():
    b = B(46)
    b.ground(0, 45, ch="S", fill="S")
    b.wall(1, 3, GROUND - 1); b.wall(2, 3, GROUND - 1)
    b.wall(44, 3, GROUND - 1); b.wall(43, 3, GROUND - 1)
    b.plat(9, 13, 11, "S"); b.plat(33, 37, 11, "S")
    b.arc(15, 9); b.arc(31, 9); b.coins(21, 25, 8)
    b.e("growth", 6, FLOOR)
    b.e("boss", 23, FLOOR)
    b.dump(LV / "level10.json", "Frostkönigs Festung", "cave", music="boss.ogg")


# --- Welt 2 -------------------------------------------------------------
def level11():
    b = B(180)
    pits = [(26, 31), (52, 58), (84, 90), (116, 122), (148, 154)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1); x = c + 1
    b.ground(x, 179)
    for x0, x1, y in [(20, 26, 10), (66, 72, 8), (100, 106, 10), (140, 146, 8)]:
        b.plat(x0, x1, y)
    b.e("mplat", 52, 11, 58, 8, 3); b.e("mplat", 116, 12, 122, 12, 3)
    b.e("spring", 24, FLOOR); b.e("spring", 82, FLOOR); b.e("spring", 146, FLOOR)
    for cx in (28, 55, 87, 119, 151):
        b.arc(cx, 8)
    b.coins(66, 72, 7); b.coins(100, 106, 9); b.coins(140, 146, 7)
    b.e("growth", 68, 6)
    for ex in (16, 44, 78, 110, 164):
        b.e("snowball", ex, FLOOR)
    for ex in (38, 96, 130):
        b.e("spiky", ex, FLOOR)
    b.e("flyer", 60, 6, 6); b.e("flyer", 128, 5, 7)
    b.e("checkpoint", 92, FLOOR); b.e("goal", 176, FLOOR)
    b.dump(LV / "level11.json", "Kraterfelder", "sunset")


def level12():
    b = B(185)
    pits = [(24, 29), (50, 56), (80, 86), (112, 118), (144, 150), (166, 171)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1, ch="I", fill="I"); x = c + 1
    b.ground(x, 184, ch="I", fill="I")
    for x0, x1, y in [(18, 24, 10), (62, 68, 9), (96, 102, 11), (130, 136, 9)]:
        b.plat(x0, x1, y, "I")
    b.e("mplat", 50, 12, 56, 8, 3); b.e("mplat", 112, 11, 118, 11, 3)
    b.e("spring", 22, FLOOR); b.e("spring", 78, FLOOR); b.e("spring", 142, FLOOR)
    for cx in (26, 53, 83, 115, 147):
        b.arc(cx, 8)
    b.e("growth", 64, 7)
    for ex in (16, 44, 90, 150, 180):
        b.e("spiky", ex, FLOOR)
    for ex in (60, 120):
        b.e("snowball", ex, FLOOR)
    b.e("flyer", 70, 6, 6); b.e("flyer", 134, 5, 7)
    b.e("checkpoint", 88, FLOOR); b.e("goal", 181, FLOOR)
    b.dump(LV / "level12.json", "Frostpalast", "ice")


def level13():
    b = B(185)
    b.ground(0, 14)
    b.ground(22, 34); b.ground(46, 60); b.ground(80, 96)
    b.ground(118, 134); b.ground(166, 184)
    b.e("mplat", 15, 12, 21, 12, 3)
    b.e("mplat", 35, 12, 45, 9, 3)
    b.e("mplat", 61, 11, 79, 11, 3)
    b.e("mplat", 97, 10, 117, 13, 3)
    b.e("mplat", 135, 12, 165, 12, 4)
    for cx in (18, 40, 70, 108, 150):
        b.arc(cx, 8)
    b.coins(24, 32, 12); b.coins(82, 94, 12)
    b.e("growth", 50, 12)
    for ex in (26, 52, 88, 124, 174):
        b.e("snowball", ex, FLOOR)
    for ex in (30, 90, 128):
        b.e("spiky", ex, FLOOR)
    b.e("flyer", 40, 6, 6); b.e("flyer", 100, 5, 8); b.e("flyer", 150, 7, 6)
    b.e("spring", 12, FLOOR); b.e("spring", 176, FLOOR)
    b.e("checkpoint", 88, FLOOR); b.e("goal", 181, FLOOR)
    for t, y in [(10, 1), (60, 2), (120, 1)]:
        b.prop("cloud", t, y)
    b.dump(LV / "level13.json", "Sternenschlucht", "night")


def level14():
    b = B(195)
    pits = [(22, 27), (42, 48), (66, 72), (92, 98), (120, 126), (150, 156), (176, 181)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1, ch="S", fill="S"); x = c + 1
    b.ground(x, 194, ch="S", fill="S")
    for x0, x1, y in [(32, 38, 10), (78, 84, 9), (104, 110, 11), (134, 140, 9)]:
        b.plat(x0, x1, y, "S")
    b.e("mplat", 42, 12, 48, 9, 3); b.e("mplat", 92, 11, 98, 11, 3)
    b.e("mplat", 150, 10, 156, 13, 3)
    b.e("spring", 20, FLOOR); b.e("spring", 90, FLOOR); b.e("spring", 148, FLOOR)
    for cx in (24, 44, 68, 94, 122, 152):
        b.arc(cx, 8)
    b.e("growth", 34, 8); b.e("growth", 136, 7)
    for ex in (16, 56, 100, 160, 188):
        b.e("snowball", ex, FLOOR)
    for ex in (36, 80, 108, 138, 178):
        b.e("spiky", ex, FLOOR)
    b.e("flyer", 50, 6, 6); b.e("flyer", 110, 5, 7); b.e("flyer", 164, 6, 6)
    b.e("checkpoint", 74, FLOOR); b.e("checkpoint", 132, FLOOR)
    b.e("goal", 191, FLOOR)
    b.dump(LV / "level14.json", "Abgrundtiefe", "cave")


def level15():
    b = B(48)
    b.ground(0, 47, ch="S", fill="S")
    b.wall(1, 3, GROUND - 1); b.wall(2, 3, GROUND - 1)
    b.wall(46, 3, GROUND - 1); b.wall(45, 3, GROUND - 1)
    b.plat(9, 13, 11, "S"); b.plat(35, 39, 11, "S")
    b.arc(16, 9); b.arc(32, 9); b.coins(22, 26, 8)
    b.e("growth", 6, FLOOR)
    b.e("boss", 24, FLOOR, "shadow")
    b.dump(LV / "level15.json", "Schattenkönigs Thron", "cave", music="boss.ogg")


# --- Welt Ägypten (Sand "A" / Sandstein "W") ----------------------------
def level16():
    b = B(170)
    pits = [(28, 32), (54, 60), (86, 91), (118, 124), (146, 151)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1, ch="A", fill="W"); x = c + 1
    b.ground(x, 169, ch="A", fill="W")
    for x0, x1, y in [(20, 26, 11), (66, 72, 10), (100, 106, 11), (132, 138, 10)]:
        b.plat(x0, x1, y, "W")
    b.e("spring", 26, FLOOR); b.e("spring", 84, FLOOR); b.e("spring", 144, FLOOR)
    b.arc(30, 8); b.arc(57, 9); b.arc(88, 8); b.arc(121, 9); b.arc(148, 8)
    b.coins(66, 72, 8); b.coins(100, 106, 9); b.coins(132, 138, 8)
    b.e("growth", 68, 8); b.e("fish", 22, 12)
    for ex in (16, 44, 78, 110, 158):
        b.e("cat", ex, FLOOR)
    for ex in (40, 96):
        b.e("snowball", ex, FLOOR)
    b.e("checkpoint", 92, FLOOR); b.e("goal", 166, FLOOR)
    for t in (10, 50, 108, 140):
        b.prop("palm", t)
    for t in (34, 90):
        b.prop("cactus", t)
    b.prop("pyramid", 74); b.prop("sphinx", 126)
    b.dump(LV / "level16.json", "Wüstensand", "egypt")


def level17():
    b = B(180)
    pits = [(24, 29), (48, 54), (78, 84), (108, 114), (140, 146), (162, 167)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1, ch="A", fill="W"); x = c + 1
    b.ground(x, 179, ch="A", fill="W")
    for x0, x1, y in [(34, 40, 10), (66, 72, 9), (96, 102, 11), (126, 132, 9)]:
        b.plat(x0, x1, y, "W")
    b.e("mplat", 48, 12, 54, 9, 3); b.e("mplat", 108, 11, 114, 11, 3)
    b.e("box", 36, 8); b.e("box", 37, 8)
    b.e("spring", 22, FLOOR); b.e("spring", 76, FLOOR); b.e("spring", 138, FLOOR)
    for cx in (26, 50, 80, 110, 143):
        b.arc(cx, 8)
    b.e("growth", 68, 7); b.e("fishrain", 100, 8)
    for ex in (16, 62, 120, 174):
        b.e("cat", ex, FLOOR)
    for ex in (44, 90, 150):
        b.e("shooter", ex, FLOOR)
    b.e("flyer", 70, 6, 6); b.e("flyer", 130, 6, 7)
    b.e("checkpoint", 86, FLOOR); b.e("goal", 176, FLOOR)
    b.prop("pyramid", 30); b.prop("pyramid", 150); b.prop("sphinx", 92)
    for t in (12, 160):
        b.prop("palm", t)
    b.dump(LV / "level17.json", "Tal der Könige", "egypt")


def level18():
    b = B(185)
    pits = [(22, 26), (44, 50), (70, 76), (98, 104), (126, 132), (156, 162)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1, ch="A", fill="W"); x = c + 1
    b.ground(x, 184, ch="A", fill="W")
    for x0, x1, y in [(32, 38, 10), (60, 66, 9), (90, 96, 11), (120, 126, 9), (150, 156, 10)]:
        b.plat(x0, x1, y, "W")
    b.e("mplat", 44, 12, 50, 9, 3); b.e("mplat", 98, 11, 104, 11, 3)
    b.e("box", 34, 7); b.e("box", 122, 7)
    b.e("spring", 20, FLOOR); b.e("spring", 88, FLOOR); b.e("spring", 148, FLOOR)
    for cx in (24, 46, 72, 100, 128, 158):
        b.arc(cx, 8)
    b.e("growth", 62, 7); b.e("fish", 34, 12)
    for ex in (16, 56, 108, 168):
        b.e("cat", ex, FLOOR)
    for ex in (36, 80, 138):
        b.e("spiky", ex, FLOOR)
    for ex in (66, 116):
        b.e("shooter", ex, FLOOR)
    b.e("flyer", 52, 6, 6); b.e("flyer", 112, 6, 7)
    b.e("checkpoint", 78, FLOOR); b.e("checkpoint", 134, FLOOR)
    b.e("goal", 181, FLOOR)
    b.prop("pyramid", 28); b.prop("sphinx", 70); b.prop("pyramid", 160)
    for t in (14, 142):
        b.prop("cactus", t)
    b.dump(LV / "level18.json", "Pyramidengruft", "egypt")


# --- Welt Weltraum (Mond "M" / Metallplatte "P") ------------------------
def level19():
    b = B(170)
    pits = [(30, 35), (58, 64), (90, 96), (122, 128), (150, 156)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1, ch="M", fill="M"); x = c + 1
    b.ground(x, 169, ch="M", fill="M")
    for x0, x1, y in [(22, 27, 11), (68, 73, 10), (100, 106, 11), (134, 139, 10)]:
        b.plat(x0, x1, y, "P")
    b.e("mplat", 58, 12, 64, 9, 3); b.e("mplat", 122, 11, 128, 11, 3)
    b.e("spring", 28, FLOOR); b.e("spring", 86, FLOOR); b.e("spring", 146, FLOOR)
    for cx in (32, 61, 93, 125, 153):
        b.arc(cx, 8)
    b.coins(68, 73, 8); b.coins(100, 106, 9)
    b.e("growth", 70, 8); b.e("fish", 24, 12)
    for ex in (16, 46, 80, 112, 158):
        b.e("alien", ex, FLOOR)
    b.e("checkpoint", 94, FLOOR); b.e("goal", 166, FLOOR)
    b.prop("rocket", 8); b.prop("meteor", 52); b.prop("meteor", 108)
    for t, y in [(20, 2), (80, 1), (140, 2)]:
        b.prop("planet", t, y)
    b.dump(LV / "level19.json", "Startrampe", "space")


def level20():
    b = B(180)
    pits = [(24, 30), (50, 57), (80, 87), (110, 117), (142, 149), (164, 170)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1, ch="M", fill="M"); x = c + 1
    b.ground(x, 179, ch="M", fill="M")
    for x0, x1, y in [(34, 40, 10), (66, 72, 9), (96, 102, 11), (126, 132, 9)]:
        b.plat(x0, x1, y, "P")
    b.e("mplat", 50, 12, 57, 9, 3); b.e("mplat", 110, 11, 117, 11, 3)
    b.e("box", 36, 8); b.e("box", 37, 8)
    b.e("spring", 22, FLOOR); b.e("spring", 78, FLOOR); b.e("spring", 140, FLOOR)
    for cx in (26, 53, 83, 113, 145):
        b.arc(cx, 8)
    b.e("growth", 68, 7); b.e("fishrain", 100, 8)
    for ex in (16, 62, 120, 174):
        b.e("alien", ex, FLOOR)
    for ex in (44, 90, 150):
        b.e("shooter", ex, FLOOR)
    b.e("flyer", 70, 6, 6); b.e("flyer", 130, 6, 7)
    b.e("checkpoint", 86, FLOOR); b.e("goal", 176, FLOOR)
    b.prop("rocket", 12); b.prop("planet", 60, 1); b.prop("meteor", 156)
    b.dump(LV / "level20.json", "Mondbasis", "space")


def level21():
    b = B(185)
    b.ground(0, 12, ch="M", fill="M")
    b.ground(150, 184, ch="M", fill="M")
    for x0, x1 in [(24, 30), (46, 52), (74, 82), (108, 116), (132, 140)]:
        b.plat(x0, x1, 12, "P")
    b.e("mplat", 13, 12, 23, 12, 3)
    b.e("mplat", 31, 12, 45, 9, 3)
    b.e("mplat", 53, 11, 73, 11, 3)
    b.e("mplat", 83, 10, 107, 13, 3)
    b.e("mplat", 117, 12, 149, 12, 4)
    for cx in (27, 49, 78, 112, 136):
        b.arc(cx, 9)
    b.e("growth", 50, 11); b.e("fish", 6, 12)
    for ex in (26, 78, 158, 178):
        b.e("alien", ex, FLOOR)
    b.e("flyer", 40, 6, 6); b.e("flyer", 96, 6, 8); b.e("flyer", 140, 8, 6)
    b.e("spring", 8, FLOOR); b.e("spring", 176, FLOOR)
    b.e("checkpoint", 78, FLOOR); b.e("goal", 181, FLOOR)
    for t, y in [(20, 1), (90, 2), (150, 1)]:
        b.prop("planet", t, y)
    b.dump(LV / "level21.json", "Sternenmeer", "space")


# --- Welt Großstadt (Asphalt "C" / Beton+Stahl "K") ---------------------
def level22():
    # Straßenzug: Laternen, Absperrungen, Roboter-Streife
    b = B(172)
    pits = [(30, 34), (56, 62), (88, 93), (120, 126), (148, 153)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1, ch="C", fill="K"); x = c + 1
    b.ground(x, 171, ch="C", fill="K")
    for x0, x1, y in [(20, 26, 11), (66, 72, 10), (100, 106, 11), (132, 138, 10)]:
        b.plat(x0, x1, y, "K")
    b.e("mplat", 56, 12, 62, 9, 3); b.e("mplat", 120, 11, 126, 11, 3)
    b.e("spring", 28, FLOOR); b.e("spring", 86, FLOOR); b.e("spring", 146, FLOOR)
    b.arc(32, 8); b.arc(59, 9); b.arc(90, 8); b.arc(123, 9); b.arc(150, 8)
    b.coins(66, 72, 8); b.coins(100, 106, 9); b.coins(132, 138, 8)
    b.e("growth", 68, 8); b.e("fish", 22, 12)
    for ex in (16, 44, 78, 110, 158):
        b.e("robot", ex, FLOOR)
    for ex in (40, 96):
        b.e("snowball", ex, FLOOR)
    b.e("checkpoint", 92, FLOOR); b.e("goal", 168, FLOOR)
    for t in (10, 50, 108, 140):
        b.prop("streetlamp", t)
    for t in (34, 90, 126):
        b.prop("barrier", t)
    b.prop("skyscraper", 74); b.prop("skyscraper", 155)
    b.dump(LV / "level22.json", "Innenstadt bei Nacht", "city")


def level23():
    # Baustelle: Stahlträger-Plattformen, Kräne, schießende Pflanzen
    b = B(182)
    pits = [(24, 29), (48, 54), (78, 84), (108, 114), (140, 146), (164, 169)]
    x = 0
    for a, c in pits:
        b.ground(x, a - 1, ch="C", fill="K"); x = c + 1
    b.ground(x, 181, ch="C", fill="K")
    for x0, x1, y in [(34, 40, 10), (66, 72, 9), (96, 102, 11), (126, 132, 9)]:
        b.plat(x0, x1, y, "K")
    b.e("mplat", 48, 12, 54, 9, 3); b.e("mplat", 108, 11, 114, 11, 3)
    b.e("box", 36, 8); b.e("box", 37, 8)
    b.e("spring", 22, FLOOR); b.e("spring", 76, FLOOR); b.e("spring", 138, FLOOR)
    for cx in (26, 51, 81, 111, 143):
        b.arc(cx, 8)
    b.e("growth", 68, 7); b.e("fishrain", 100, 8)
    for ex in (16, 62, 120, 176):
        b.e("robot", ex, FLOOR)
    for ex in (44, 90, 150):
        b.e("shooter", ex, FLOOR)
    b.e("flyer", 70, 6, 6); b.e("flyer", 130, 6, 7)
    b.e("checkpoint", 86, FLOOR); b.e("goal", 178, FLOOR)
    b.prop("crane", 30); b.prop("crane", 150)
    for t in (12, 92, 160):
        b.prop("barrier", t)
    b.prop("skyscraper", 116)
    b.dump(LV / "level23.json", "Wolkenkratzer-Baustelle", "city")


def level24():
    # Dächer-Parcours hoch über der Stadt: viele bewegliche Plattformen
    b = B(185)
    b.ground(0, 12, ch="C", fill="K")
    b.ground(150, 184, ch="C", fill="K")
    for x0, x1 in [(24, 30), (46, 52), (74, 82), (108, 116), (132, 140)]:
        b.plat(x0, x1, 12, "K")
    b.e("mplat", 13, 12, 23, 12, 3)
    b.e("mplat", 31, 12, 45, 9, 3)
    b.e("mplat", 53, 11, 73, 11, 3)
    b.e("mplat", 83, 10, 107, 13, 3)
    b.e("mplat", 117, 12, 149, 12, 4)
    for cx in (27, 49, 78, 112, 136):
        b.arc(cx, 9)
    b.e("growth", 50, 11); b.e("fish", 6, 12)
    for ex in (26, 78, 158, 178):
        b.e("robot", ex, FLOOR)
    b.e("flyer", 40, 6, 6); b.e("flyer", 96, 6, 8); b.e("flyer", 140, 8, 6)
    b.e("spring", 8, FLOOR); b.e("spring", 176, FLOOR)
    b.e("checkpoint", 78, FLOOR); b.e("goal", 181, FLOOR)
    b.prop("skyscraper", 4); b.prop("skyscraper", 166)
    b.prop("crane", 88); b.prop("streetlamp", 158)
    b.dump(LV / "level24.json", "Über den Dächern", "city")


def main():
    print("Baue Level ->", LV)
    for fn in (level1, level2, level3, level4, level5, level6, level7, level8,
               level9, level10, level11, level12, level13, level14, level15,
               level16, level17, level18, level19, level20, level21,
               level22, level23, level24):
        fn()
    print("Fertig.")


if __name__ == "__main__":
    main()
