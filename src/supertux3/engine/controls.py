"""Zentrale Steuerung: Tastatur + Gamepad.

`nav(event)` übersetzt Tastatur- und Joystick-Ereignisse in abstrakte
Menü-Aktionen ('up'/'down'/'left'/'right'/'confirm'/'back'/'pause').
Für das laufende Spiel liest der Spieler Achsen/Buttons direkt (siehe Helfer).
"""
from __future__ import annotations

import pygame

_KEY_NAV = {
    pygame.K_UP: "up", pygame.K_w: "up",
    pygame.K_DOWN: "down", pygame.K_s: "down",
    pygame.K_LEFT: "left", pygame.K_a: "left",
    pygame.K_RIGHT: "right", pygame.K_d: "right",
    pygame.K_RETURN: "confirm", pygame.K_SPACE: "confirm",
    pygame.K_ESCAPE: "back",
}

# Gamepad-Buttons (Xbox-Layout)
BTN_A, BTN_B, BTN_BACK, BTN_START = 0, 1, 6, 7


def nav(event) -> str | None:
    if event.type == pygame.KEYDOWN:
        return _KEY_NAV.get(event.key)
    if event.type == pygame.JOYBUTTONDOWN:
        if event.button in (BTN_A,):
            return "confirm"
        if event.button in (BTN_B, BTN_BACK):
            return "back"
        if event.button == BTN_START:
            return "pause"
    if event.type == pygame.JOYHATMOTION:
        hx, hy = event.value
        if hx < 0:
            return "left"
        if hx > 0:
            return "right"
        if hy > 0:
            return "up"
        if hy < 0:
            return "down"
    return None


# --- Gameplay-Helfer (kontinuierlich) -----------------------------------
DEAD = 0.4


def move_x(joysticks) -> int:
    for js in joysticks:
        try:
            ax = js.get_axis(0) if js.get_numaxes() > 0 else 0.0
            hx = js.get_hat(0)[0] if js.get_numhats() > 0 else 0
        except pygame.error:
            continue
        if ax < -DEAD or hx < 0:
            return -1
        if ax > DEAD or hx > 0:
            return 1
    return 0


def want_jump(joysticks) -> bool:
    for js in joysticks:
        try:
            if js.get_numbuttons() > BTN_A and js.get_button(BTN_A):
                return True
        except pygame.error:
            continue
    return False


def want_duck(joysticks) -> bool:
    for js in joysticks:
        try:
            ay = js.get_axis(1) if js.get_numaxes() > 1 else 0.0
            hy = js.get_hat(0)[1] if js.get_numhats() > 0 else 0
        except pygame.error:
            continue
        if ay > DEAD or hy < 0:
            return True
    return False
