#!/usr/bin/env python3
"""Exportiert ein SuperTux3-JSON-Level in ein Tiled-TMX (und zurück ladbar).

Dient als Nachweis für den TMX-Import (src/supertux3/world/tmx.py) und als
Startpunkt, um Level in Tiled weiterzubearbeiten.

Nutzung:  python tools/json_to_tmx.py levels/level1.json [ausgabe.tmx]
Konvention: firstgid=1, GID N (1..6) == Spiel-Kachel-ID N.
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TILE = 32
CHAR_TO_GID = {".": 0, " ": 0, "G": 1, "D": 2, "B": 3, "#": 4, "S": 5, "I": 6}


def _add_props(parent, props: dict):
    if not props:
        return
    pe = ET.SubElement(parent, "properties")
    for k, v in props.items():
        ET.SubElement(pe, "property", name=str(k), value=str(v))


def convert(data: dict) -> ET.ElementTree:
    rows = data.get("solid", [])
    h = len(rows)
    w = max((len(r) for r in rows), default=0)

    m = ET.Element("map", {
        "version": "1.10", "orientation": "orthogonal", "renderorder": "right-down",
        "width": str(w), "height": str(h),
        "tilewidth": str(TILE), "tileheight": str(TILE), "infinite": "0",
    })
    _add_props(m, {
        "name": data.get("name", "Level"),
        "theme": data.get("theme", "grass"),
        "music": data.get("music", ""),
        "spawn_x": data.get("spawn", [2, 14])[0],
        "spawn_y": data.get("spawn", [2, 14])[1],
    })

    ts = ET.SubElement(m, "tileset", {
        "firstgid": "1", "name": "supertux3", "tilewidth": str(TILE),
        "tileheight": str(TILE), "tilecount": "6", "columns": "6"})
    ET.SubElement(ts, "image", {
        "source": "../assets/images/tiles/tileset.png",
        "width": str(TILE * 7), "height": str(TILE)})

    layer = ET.SubElement(m, "layer", {"id": "1", "name": "solid",
                                       "width": str(w), "height": str(h)})
    gids = []
    for r in range(h):
        row = rows[r]
        for c in range(w):
            ch = row[c] if c < len(row) else "."
            gids.append(str(CHAR_TO_GID.get(ch, 0)))
    data_el = ET.SubElement(layer, "data", {"encoding": "csv"})
    lines = [",".join(gids[r * w:(r + 1) * w]) for r in range(h)]
    data_el.text = "\n" + ",\n".join(lines) + "\n"

    # Objekte
    ent_grp = ET.SubElement(m, "objectgroup", {"id": "2", "name": "entities"})
    oid = 1
    for e in data.get("entities", []):
        kind, tx, ty = e[0], e[1], e[2]
        obj = ET.SubElement(ent_grp, "object", {
            "id": str(oid), "type": kind,
            "x": str(tx * TILE), "y": str(ty * TILE)})
        oid += 1
        if kind == "mplat":
            _add_props(obj, {"tx2": e[3] if len(e) > 3 else tx,
                             "ty2": e[4] if len(e) > 4 else ty,
                             "wtiles": e[5] if len(e) > 5 else 3})
        elif kind == "flyer" and len(e) > 3:
            _add_props(obj, {"patrol": e[3]})

    prop_grp = ET.SubElement(m, "objectgroup", {"id": "3", "name": "props"})
    for p in data.get("props", []):
        ET.SubElement(prop_grp, "object", {
            "id": str(oid), "type": p[0],
            "x": str(p[1] * TILE), "y": str(p[2] * TILE)})
        oid += 1

    ET.indent(m, space=" ")
    return ET.ElementTree(m)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".tmx")
    with open(src, "r", encoding="utf-8") as f:
        data = json.load(f)
    convert(data).write(out, encoding="unicode", xml_declaration=True)
    print(f"geschrieben: {out}")


if __name__ == "__main__":
    main()
