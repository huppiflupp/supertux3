#!/usr/bin/env python3
"""Erzeugt das App-Icon (aus dem Pengu-Sprite) in mehreren Größen.

Ausgabe: assets/icon/supertux3-{256,128,64}.png
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "assets" / "images"
OUT = ROOT / "assets" / "icon"


def build(size=256):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # abgerundeter Himmelshintergrund
    for y in range(size):
        f = y / (size - 1)
        col = (int(120 + 40 * f), int(170 + 40 * f), 255)
        d.line([(0, y), (size, y)], fill=col)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1],
                                           radius=size // 6, fill=255)
    img.putalpha(mask)
    d = ImageDraw.Draw(img)
    # Hügel
    d.ellipse([-size * 0.3, size * 0.62, size * 1.3, size * 1.5], fill=(96, 196, 96, 255))
    d.ellipse([size * 0.4, size * 0.72, size * 1.5, size * 1.6], fill=(80, 178, 84, 255))
    # Pengu (aus erstem Frame von pengu_big) mittig-unten
    pengu = Image.open(IMG / "characters" / "pengu_big.png").convert("RGBA")
    frame = pengu.crop((0, 0, 60, 72))
    scale = int(size * 0.62) / frame.height
    fw, fh = int(frame.width * scale), int(frame.height * scale)
    frame = frame.resize((fw, fh), Image.LANCZOS)
    img.alpha_composite(frame, ((size - fw) // 2, int(size * 0.30)))
    # Münze
    coin = Image.open(IMG / "collectibles" / "coin.png").convert("RGBA").crop((0, 0, 24, 24))
    cs = int(size * 0.18)
    coin = coin.resize((cs, cs), Image.LANCZOS)
    img.alpha_composite(coin, (int(size * 0.12), int(size * 0.24)))
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base = build(256)
    for s in (256, 128, 64):
        out = base.resize((s, s), Image.LANCZOS)
        out.save(OUT / f"supertux3-{s}.png")
        print(f"  icon/supertux3-{s}.png")


if __name__ == "__main__":
    main()
