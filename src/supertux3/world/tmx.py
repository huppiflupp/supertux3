"""Minimaler Tiled-TMX-Import.

Unterstützt eine CSV-kodierte Kachel-Ebene ("solid") und Objektgruppen
("entities", "props"). Erwartete Konvention (siehe tools/json_to_tmx.py):

- Ein Kachelsatz mit firstgid=1; GID N (1..6) == Spiel-Kachel-ID N
  (1=Gras,2=Erde,3=Ziegel,4=Hartblock,5=Stein,6=Eis), GID 0 = leer.
- Map-Eigenschaften: name, theme, music, spawn_x, spawn_y.
- Objekte: `type`/`class` = Objektart; Position (x,y) in Pixeln -> Kachel via
  round(x/tw), round(y/th). Zusatzparameter als <properties> (tx2, ty2,
  wtiles, patrol).

Damit lassen sich in Tiled gebaute Level direkt laden.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

GID_TO_CHAR = {1: "G", 2: "D", 3: "B", 4: "#", 5: "S", 6: "I"}


def _props(elem) -> dict:
    out = {}
    pr = elem.find("properties")
    if pr is None:
        return out
    for p in pr.findall("property"):
        name = p.get("name")
        val = p.get("value", p.text)
        if val is None:
            continue
        try:
            out[name] = int(val)
        except ValueError:
            try:
                out[name] = float(val)
            except ValueError:
                out[name] = val
    return out


def parse_tmx(path: str | Path) -> dict:
    root = ET.parse(path).getroot()
    w = int(root.get("width"))
    h = int(root.get("height"))
    tw = int(root.get("tilewidth", 32))
    th = int(root.get("tileheight", 32))
    meta = _props(root)

    # Kachel-Ebene "solid"
    rows = ["." * w for _ in range(h)]
    for layer in root.findall("layer"):
        if layer.get("name") != "solid":
            continue
        data = layer.find("data")
        raw = (data.text or "").replace("\n", " ").strip().strip(",")
        gids = [int(x) for x in raw.replace(" ", "").split(",") if x != ""]
        grid = []
        for r in range(h):
            chars = []
            for c in range(w):
                gid = gids[r * w + c] if r * w + c < len(gids) else 0
                chars.append(GID_TO_CHAR.get(gid, "."))
            grid.append("".join(chars))
        rows = grid

    entities, props = [], []
    for grp in root.findall("objectgroup"):
        gname = grp.get("name", "")
        for obj in grp.findall("object"):
            kind = obj.get("type") or obj.get("class")
            if not kind:
                continue
            tx = round(float(obj.get("x", 0)) / tw)
            ty = round(float(obj.get("y", 0)) / th)
            pp = _props(obj)
            if gname == "props":
                props.append([kind, tx, ty])
            elif kind == "mplat":
                entities.append(["mplat", tx, ty, int(pp.get("tx2", tx)),
                                 int(pp.get("ty2", ty)), int(pp.get("wtiles", 3))])
            elif kind == "flyer":
                entities.append(["flyer", tx, ty, int(pp.get("patrol", 6))])
            else:
                entities.append([kind, tx, ty])

    return {
        "name": meta.get("name", Path(path).stem),
        "theme": meta.get("theme", "grass"),
        "music": meta.get("music"),
        "spawn": [int(meta.get("spawn_x", 2)), int(meta.get("spawn_y", 14))],
        "solid": rows,
        "props": props,
        "entities": entities,
    }
