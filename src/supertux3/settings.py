"""Zentrale Konstanten und Pfade für SuperTux3.

Alle Physikwerte sind in Pixeln pro Sekunde (bzw. pro Sekunde^2) angegeben und
werden mit einem festen Zeitschritt (FIXED_DT) integriert, damit sich das Spiel
auf jeder Hardware identisch anfühlt.
"""
from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

# --- Pfade ---------------------------------------------------------------
PKG_DIR = Path(__file__).resolve().parent


def _find_root() -> Path:
    """Findet das Verzeichnis mit assets/ und levels/ (Dev-Baum oder Install)."""
    env = os.environ.get("SUPERTUX3_DATA")
    cands = [Path(env)] if env else []
    cands += [PKG_DIR.parent.parent, PKG_DIR, PKG_DIR.parent,
              Path(sys.prefix) / "share" / "supertux3",
              Path("/usr/share/supertux3"), Path("/usr/local/share/supertux3"),
              Path("/app/share/supertux3")]
    for c in cands:
        if (c / "assets").is_dir() and (c / "levels").is_dir():
            return c
    return PKG_DIR.parent.parent


PROJECT_ROOT = _find_root()
ASSET_DIR = PROJECT_ROOT / "assets"
IMAGE_DIR = ASSET_DIR / "images"
AUDIO_DIR = ASSET_DIR / "audio"
FONT_DIR = ASSET_DIR / "fonts"
LEVEL_DIR = PROJECT_ROOT / "levels"


def _user_data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    d = Path(base) / "supertux3"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        d = Path.home() / ".supertux3"
        d.mkdir(parents=True, exist_ok=True)
    return d


USER_DATA_DIR = _user_data_dir()
USER_LEVEL_DIR = USER_DATA_DIR / "levels"

# --- Plattform / Performance --------------------------------------------
IS_ARM = platform.machine().lower() in {"aarch64", "arm64", "armv7l", "armv6l"}
# Grafikqualität: "smooth" (geglättet, Desktop) | "fast" (nearest, Pi/schwache HW)
DEFAULT_QUALITY = "fast" if IS_ARM else "smooth"
DEFAULT_FPS = 60

# --- Fenster / Rendering -------------------------------------------------
GAME_TITLE = "SuperTux3"
# Interne Renderauflösung. Das Sichtfeld bleibt 30x16.9 Kacheln (wie zuvor bei
# 480x270 / 16px), nur alles in doppelter Auflösung mit detaillierterer Grafik.
VIRTUAL_W = 960
VIRTUAL_H = 540
WINDOW_SCALE = 2               # bevorzugter Start-Skalierungsfaktor
FPS = 60
FIXED_DT = 1.0 / 60.0          # fester Physik-Zeitschritt

# --- Welt ----------------------------------------------------------------
TILE = 32                      # Kachelgröße in Pixeln (wie SuperTux2)

# --- Physik (px pro Sekunde) --------------------------------------------
# Werte skalieren mit TILE (32/16 = 2x), damit Sprunghöhe/Tempo IN KACHELN und
# damit das Spielgefühl identisch zum 16px-Prototyp bleiben.
GRAVITY = 2200.0
MAX_FALL_SPEED = 1120.0
MOVE_ACCEL = 1800.0
AIR_ACCEL = 1300.0
MAX_RUN_SPEED = 260.0
GROUND_FRICTION = 2000.0
JUMP_SPEED = 720.0            # Anfangsgeschwindigkeit nach oben
JUMP_CUTOFF = 0.45           # Faktor, wenn Sprungtaste früh losgelassen wird
COYOTE_TIME = 0.08           # noch springen dürfen kurz nach Kantenabgang (zeitbasiert)
JUMP_BUFFER = 0.10           # Sprungeingabe kurz vorm Landen puffern (zeitbasiert)
STOMP_BOUNCE = 520.0         # Absprung nach Gegner-Stampfen
SPRING_SPEED = 1240.0        # Absprung von einer Sprungfeder

# --- Farben (Fallback / UI) ---------------------------------------------
SKY_TOP = (92, 148, 252)
SKY_BOTTOM = (170, 210, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
UI_SHADOW = (30, 30, 40)

# --- Gameplay ------------------------------------------------------------
START_LIVES = 3

# Level-Reihenfolge (Dateien in levels/)
LEVEL_FILES = [f"level{i}.json" for i in range(1, 25)]

# Geheimlevel (nicht in der linearen Reihe; via verstecktem Ausgang erreichbar)
SECRET_LEVELS = ["secret1.json"]
