#!/usr/bin/env python3
"""FLUX-Greenscreen-Bilder freistellen und ins Spiel einsetzen.

FLUX liefert deckende Bilder ohne Alpha. Die per FLUX auf sattem Chroma-Green
(#00b140) erzeugten Objekte/Posen (in assets/images/characters/flux_src/…)
werden hier freigestellt:

- Rand-Flood-Fill entfernt nur den mit dem Bildrand verbundenen grünen
  Hintergrund -> grüne Objektteile (Baumkrone, Kaktus) bleiben erhalten.
- Grün-Entfärbung (Despill) dämpft grüne Farbsäume an den Kanten.
- Zuschnitt auf die Objekt-Bounding-Box, Skalierung auf die vorhandene
  Spielgröße (aus dem bisherigen prozeduralen PNG übernommen).

Nutzung:
  python tools/asset_pipeline/flux_cutout.py props    # Deko-Objekte einsetzen
  python tools/asset_pipeline/flux_cutout.py pengu     # Pinguin-Sheet bauen
  python tools/asset_pipeline/flux_cutout.py all
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "assets" / "images"
SRC = IMG / "characters" / "flux_src"


def cutout(img: Image.Image, thresh: int = 70, feather: float = 1.1,
           kill_green: bool = False) -> Image.Image:
    """Greenscreen entfernen (nur randverbundenes Grün) + Despill + Zuschnitt.

    kill_green: zusätzlich ALLE grünlichen Pixel entfernen – nur für Motive OHNE
    grüne Bestandteile (z.B. Pinguin), NICHT für Bäume/Büsche/Kaktus.
    """
    img = img.convert("RGBA")
    w, h = img.size
    work = img.convert("RGB").copy()
    seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
             (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]
    for s in seeds:
        try:
            ImageDraw.floodfill(work, s, (255, 0, 255), thresh=thresh)
        except Exception:
            pass
    warr = np.asarray(work).astype(np.int16)
    is_bg = ((np.abs(warr[..., 0] - 255) < 8) &
             (np.abs(warr[..., 1] - 0) < 8) &
             (np.abs(warr[..., 2] - 255) < 8))
    rgba = np.asarray(img).astype(np.uint8).copy()
    r = rgba[..., 0].astype(int); g = rgba[..., 1].astype(int); b = rgba[..., 2].astype(int)
    if kill_green:
        greenness = g - np.maximum(r, b)
        is_bg = is_bg | (greenness > 14)
    # Despill: grüne Farbsäume dämpfen
    mx = np.maximum(r, b)
    spill = (g > mx + 14) & (~is_bg)
    rgba[..., 1] = np.where(spill, (mx + 14), g).astype(np.uint8)
    alpha = np.where(is_bg, 0, 255).astype(np.uint8)
    a_img = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(feather))
    out = Image.fromarray(rgba, "RGBA")
    out.putalpha(a_img)
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    return out


def fit(img: Image.Image, tw: int, th: int) -> Image.Image:
    w, h = img.size
    s = min(tw / w, th / h)
    return img.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)


def frame(pose: Image.Image, fw: int, fh: int, sx=1.0, sy=1.0) -> Image.Image:
    """Pose unten-mittig in ein Frame fw x fh setzen (mit optionalem Squash)."""
    p = fit(pose, int(fw * sx), int(fh * sy))
    f = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    f.alpha_composite(p, ((fw - p.width) // 2, fh - p.height))
    return f


# --- Deko-Objekte -------------------------------------------------------
DEFAULT_SIZE = {  # Fallback, falls kein prozedurales PNG existiert
    "tree": (64, 96), "bush": (48, 32), "cloud": (96, 48), "palm": (56, 88),
    "cactus": (32, 52), "pyramid": (96, 84), "sphinx": (96, 56),
    "rocket": (48, 96), "planet": (64, 64), "meteor": (28, 24),
    "skyscraper": (96, 150), "crane": (96, 128), "streetlamp": (28, 104),
    "barrier": (32, 44),
}


def build_props():
    pdir = SRC / "props"
    if not pdir.is_dir():
        print("kein flux_src/props – übersprungen")
        return
    for src in sorted(pdir.glob("*.png")):
        name = src.stem
        dst = IMG / "props" / f"{name}.png"
        tw, th = DEFAULT_SIZE.get(name, (64, 64))
        if dst.exists():                     # vorhandene Spielgröße übernehmen
            tw, th = Image.open(dst).size
        co = cutout(Image.open(src))
        fitted = fit(co, tw, th)
        canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        canvas.alpha_composite(fitted, ((tw - fitted.width) // 2, th - fitted.height))
        canvas.save(dst)
        print(f"  props/{name}.png  {canvas.size}  (aus {src.name})")


# --- Pinguin-Sheet aus 4 Posen ------------------------------------------
def _pose(name):
    # Pinguin hat kein Grün -> kill_green entfernt auch den grünen Bodenschatten
    p = SRC / f"pengu_{name}.png"
    return cutout(Image.open(p), kill_green=True) if p.exists() else None


def build_pengu():
    stand = _pose("stand"); walk = _pose("walk"); jump = _pose("jump"); duck = _pose("duck")
    if stand is None:
        print("keine Pinguin-Posen (flux_src/pengu_stand.png fehlt) – übersprungen")
        return
    walk = walk or stand; jump = jump or stand; duck = duck or stand
    # FLUX-Pinguin schaut nach links; das Spiel erwartet Basis nach RECHTS
    # (facing<0 wird gespiegelt). Deshalb alle Posen einmal horizontal spiegeln.
    stand, walk, jump, duck = (im.transpose(Image.FLIP_LEFT_RIGHT)
                               for im in (stand, walk, jump, duck))

    def sheet(fw, fh, path):
        # 10 Frames: idle0,idle1,walk0,walk1,walk2,walk3,jump,fall,duck,throw
        frames = [
            frame(stand, fw, fh),
            frame(stand, fw, fh, sy=0.97),          # idle1 (Atmen)
            frame(walk, fw, fh, sx=1.02),           # walk0
            frame(stand, fw, fh),                   # walk1 (Kontakt)
            frame(walk, fw, fh, sx=0.98),           # walk2
            frame(stand, fw, fh, sy=0.98),          # walk3
            frame(jump, fw, fh, sy=1.05),           # jump
            frame(jump, fw, fh, sy=0.95),           # fall
            frame(duck, fw, fh),                    # duck
            frame(jump, fw, fh),                    # throw (Näherung)
        ]
        sh = Image.new("RGBA", (fw * len(frames), fh), (0, 0, 0, 0))
        for i, fr in enumerate(frames):
            sh.alpha_composite(fr, (i * fw, 0))
        sh.save(path)
        print(f"  {path.relative_to(IMG)}  {sh.size}")

    sheet(40, 48, IMG / "characters" / "pengu.png")
    sheet(60, 72, IMG / "characters" / "pengu_big.png")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("Freistellen ->", IMG)
    if mode in ("props", "all"):
        build_props()
    if mode in ("pengu", "all"):
        build_pengu()
    print("Fertig.")


if __name__ == "__main__":
    main()
