"""Game: Fenster, Hauptschleife (fester Zeitschritt) und Verdrahtung.

Gerendert wird in eine interne Fläche (VIRTUAL_W x VIRTUAL_H) und danach
seitenverhältnistreu auf das (frei skalierbare) Fenster gebracht.
"""
from __future__ import annotations

import pygame

from .settings import (
    VIRTUAL_W, VIRTUAL_H, WINDOW_SCALE, FPS, FIXED_DT, GAME_TITLE, START_LIVES,
)
from .assets import Assets
from .engine.audio import AudioManager
from .engine.scene import SceneManager


class Game:
    def __init__(self) -> None:
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
        except pygame.error:
            pass
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass

        # Startfenstergröße = größter Faktor, der auf den Desktop passt
        info = pygame.display.Info()
        dw, dh = info.current_w, info.current_h
        scale = WINDOW_SCALE
        while scale > 1 and (VIRTUAL_W * scale > dw or VIRTUAL_H * scale > dh - 60):
            scale -= 1
        self._windowed_size = (VIRTUAL_W * scale, VIRTUAL_H * scale)
        self.fullscreen = False
        self.window = pygame.display.set_mode(self._windowed_size, pygame.RESIZABLE, vsync=1)
        pygame.display.set_caption(GAME_TITLE)

        # interne Renderfläche
        self.screen = pygame.Surface((VIRTUAL_W, VIRTUAL_H)).convert()

        self.assets = Assets()
        self.assets.load()
        self.audio = AudioManager()
        self._load_audio()

        self.lives = START_LIVES
        self.running = True
        self.scenes = SceneManager(self)

        from .scenes.menu import MenuScene
        self.scenes.switch(MenuScene(self))

    def _load_audio(self) -> None:
        for name in ("jump", "coin", "stomp", "hurt", "win"):
            self.audio.load_sfx(name, f"{name}.wav")

    def _toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN, vsync=1)
        else:
            self.window = pygame.display.set_mode(self._windowed_size, pygame.RESIZABLE, vsync=1)

    def _present(self) -> None:
        w, h = self.window.get_size()
        s = min(w / VIRTUAL_W, h / VIRTUAL_H)
        tw, th = max(1, int(VIRTUAL_W * s)), max(1, int(VIRTUAL_H * s))
        scaled = pygame.transform.smoothscale(self.screen, (tw, th))
        self.window.fill((0, 0, 0))
        self.window.blit(scaled, ((w - tw) // 2, (h - th) // 2))
        pygame.display.flip()

    def run(self) -> None:
        clock = pygame.time.Clock()
        acc = 0.0
        while self.running:
            acc += min(clock.tick(FPS) / 1000.0, 0.10)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self._toggle_fullscreen()
                elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self._windowed_size = (event.w, event.h)
                else:
                    self.scenes.handle_event(event)

            steps = 0
            while acc >= FIXED_DT and steps < 5:
                self.scenes.update(FIXED_DT)
                acc -= FIXED_DT
                steps += 1
            if steps == 5:
                acc = 0.0

            self.scenes.draw(self.screen)
            self._present()

        pygame.quit()
