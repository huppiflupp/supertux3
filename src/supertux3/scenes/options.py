"""Optionsmenü: Grafik, Bildrate, Vollbild, Lautstärke, Ton."""
from __future__ import annotations

import pygame

from ..engine.scene import Scene
from ..engine.controls import nav
from ..settings import VIRTUAL_W, VIRTUAL_H, WHITE, UI_SHADOW


class OptionsScene(Scene):
    def __init__(self, game, back_scene=None):
        super().__init__(game)
        self.back_scene = back_scene

    def on_enter(self):
        self.title_font = pygame.font.Font(None, 72)
        self.font = pygame.font.Font(None, 40)
        self.small = pygame.font.Font(None, 26)
        self.sel = 0
        self.items = ["Grafik", "Bildrate", "Vollbild", "Musik", "Ton",
                      "Steuerung", "Zurück"]

    # --- Werte -------------------------------------------------------
    def _value(self, item):
        g = self.game
        if item == "Grafik":
            return "Hoch (glatt)" if g.quality == "smooth" else "Schnell (Pi)"
        if item == "Bildrate":
            return f"{g.fps_cap} FPS"
        if item == "Vollbild":
            return "An" if g.fullscreen else "Aus"
        if item == "Musik":
            return f"{int(round(g.audio.music_volume * 100))} %"
        if item == "Ton":
            return "Aus (stumm)" if g.audio.muted else "An"
        return ""

    def _change(self, item, d):
        g = self.game
        if item == "Grafik":
            g.quality = "fast" if g.quality == "smooth" else "smooth"
        elif item == "Bildrate":
            g.fps_cap = 30 if g.fps_cap == 60 else 60
        elif item == "Vollbild":
            g._toggle_fullscreen()
        elif item == "Musik":
            g.audio.change_music_volume(0.1 * d)
        elif item == "Ton":
            g.audio.toggle_mute()
        g.save_progress()

    def _leave(self):
        target = self.back_scene
        if target is None:
            from .menu import MenuScene
            target = MenuScene(self.game)
        self.game.scenes.switch(target)

    # --- Events ------------------------------------------------------
    def handle_event(self, event):
        act = nav(event)
        item = self.items[self.sel]
        if act == "up":
            self.sel = (self.sel - 1) % len(self.items)
        elif act == "down":
            self.sel = (self.sel + 1) % len(self.items)
        elif act == "left":
            if item != "Zurück":
                self._change(item, -1)
        elif act == "right":
            if item != "Zurück":
                self._change(item, +1)
        elif act == "confirm":
            if item == "Zurück":
                self._leave()
            elif item == "Steuerung":
                from .keybind import KeybindScene
                self.game.scenes.switch(KeybindScene(self.game))
            else:
                self._change(item, +1)
        elif act == "back":
            self._leave()

    # --- Zeichnen ----------------------------------------------------
    def draw(self, surface):
        surface.fill((34, 48, 78))
        for i in range(0, VIRTUAL_H, 4):
            c = 30 + int(26 * i / VIRTUAL_H)
            pygame.draw.line(surface, (c - 8, c + 8, c + 36), (0, i), (VIRTUAL_W, i))
        self._center(surface, "Optionen", self.title_font, (255, 240, 120), 70)

        y0 = 160
        for i, item in enumerate(self.items):
            y = y0 + i * 56
            selected = i == self.sel
            col = (255, 236, 130) if selected else WHITE
            prefix = "> " if selected else "  "
            label = self.font.render(prefix + item, True, col)
            surface.blit(self.font.render(prefix + item, True, UI_SHADOW),
                         (VIRTUAL_W // 2 - 260 + 2, y + 2))
            surface.blit(label, (VIRTUAL_W // 2 - 260, y))
            if item != "Zurück":
                val = self.font.render(self._value(item), True, col)
                surface.blit(val, (VIRTUAL_W // 2 + 40, y))

        self._center(surface, "Hoch/Runter wählen · Links/Rechts ändern · ESC zurück",
                     self.small, (210, 220, 240), VIRTUAL_H - 26)

    def _center(self, surface, text, font, color, y):
        img = font.render(text, True, color)
        rect = img.get_rect(center=(VIRTUAL_W // 2, y))
        surface.blit(font.render(text, True, UI_SHADOW), rect.move(2, 2))
        surface.blit(img, rect)
