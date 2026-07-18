"""Speicherstand: Fortschritt, Bestwerte (Münzen), Audio-Einstellungen.

Liegt im plattformüblichen Datenverzeichnis (XDG), fällt notfalls auf ein
verstecktes Verzeichnis im Home zurück. Fehlertolerant: defektes/leeres File
ergibt Standardwerte statt eines Absturzes.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_DEFAULT = {
    "unlocked": 0,          # höchster freigeschalteter Level-Index
    "best_coins": {},       # {"0": 12, "1": 30, ...}
    "music_volume": 0.5,
    "muted": False,
}


def _save_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    d = Path(base) / "supertux3"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        d = Path.home() / ".supertux3"
        d.mkdir(parents=True, exist_ok=True)
    return d


SAVE_PATH = _save_dir() / "save.json"


def load() -> dict:
    data = dict(_DEFAULT)
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            stored = json.load(f)
        if isinstance(stored, dict):
            data.update(stored)
            data["best_coins"] = {str(k): int(v) for k, v in
                                  dict(stored.get("best_coins", {})).items()}
    except (OSError, ValueError, TypeError):
        pass
    return data


def save(data: dict) -> None:
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
    except OSError:
        pass
