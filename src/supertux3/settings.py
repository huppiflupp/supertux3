"""Zentrale Konstanten und Pfade für SuperTux3.

Alle Physikwerte sind in Pixeln pro Sekunde (bzw. pro Sekunde^2) angegeben und
werden mit einem festen Zeitschritt (FIXED_DT) integriert, damit sich das Spiel
auf jeder Hardware identisch anfühlt.
"""
from __future__ import annotations

from pathlib import Path

# --- Pfade ---------------------------------------------------------------
PKG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PKG_DIR.parent.parent
ASSET_DIR = PROJECT_ROOT / "assets"
IMAGE_DIR = ASSET_DIR / "images"
AUDIO_DIR = ASSET_DIR / "audio"
FONT_DIR = ASSET_DIR / "fonts"
LEVEL_DIR = PROJECT_ROOT / "levels"

# --- Fenster / Rendering -------------------------------------------------
GAME_TITLE = "SuperTux3"
# Interne Renderauflösung (wird auf die Fenstergröße hochskaliert -> Pixel-Look)
VIRTUAL_W = 480
VIRTUAL_H = 270
WINDOW_SCALE = 3               # Startfenster = VIRTUAL * SCALE
FPS = 60
FIXED_DT = 1.0 / 60.0          # fester Physik-Zeitschritt

# --- Welt ----------------------------------------------------------------
TILE = 16                      # Kachelgröße in Pixeln (interne Auflösung)

# --- Physik (px pro Sekunde) --------------------------------------------
GRAVITY = 1100.0
MAX_FALL_SPEED = 560.0
MOVE_ACCEL = 900.0
AIR_ACCEL = 650.0
MAX_RUN_SPEED = 130.0
GROUND_FRICTION = 1000.0
JUMP_SPEED = 360.0             # Anfangsgeschwindigkeit nach oben
JUMP_CUTOFF = 0.45            # Faktor, wenn Sprungtaste früh losgelassen wird
COYOTE_TIME = 0.08            # noch springen dürfen kurz nach Kantenabgang
JUMP_BUFFER = 0.10           # Sprungeingabe kurz vorm Landen puffern
STOMP_BOUNCE = 260.0          # Absprung nach Gegner-Stampfen

# --- Farben (Fallback / UI) ---------------------------------------------
SKY_TOP = (92, 148, 252)
SKY_BOTTOM = (170, 210, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
UI_SHADOW = (30, 30, 40)

# --- Gameplay ------------------------------------------------------------
START_LIVES = 3
