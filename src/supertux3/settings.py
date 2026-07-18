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
LEVEL_FILES = [
    "level1.json", "level2.json", "level3.json",
    "level4.json", "level5.json", "level6.json",
]
