"""Game: Fenster, Hauptschleife (fester Zeitschritt) und Verdrahtung."""
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
        # Audio möglichst früh mit kleinem Puffer für geringe Latenz
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
        except pygame.error:
            pass
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass

        flags = pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode(
            (VIRTUAL_W, VIRTUAL_H), flags, vsync=1)
        pygame.display.set_caption(GAME_TITLE)

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
        self.audio.load_sfx("jump", "jump.wav")
        self.audio.load_sfx("coin", "coin.wav")
        self.audio.load_sfx("stomp", "stomp.wav")
        self.audio.load_sfx("hurt", "hurt.wav")
        self.audio.load_sfx("win", "win.wav")

    def run(self) -> None:
        clock = pygame.time.Clock()
        acc = 0.0
        while self.running:
            frame = min(clock.tick(FPS) / 1000.0, 0.10)
            acc += frame

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                else:
                    self.scenes.handle_event(event)

            steps = 0
            while acc >= FIXED_DT and steps < 5:
                self.scenes.update(FIXED_DT)
                acc -= FIXED_DT
                steps += 1
            if steps == 5:
                acc = 0.0  # Aufhol-Spirale vermeiden

            self.scenes.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
