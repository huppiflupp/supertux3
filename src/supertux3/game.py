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
from .engine import save as savemod


class Game:
    def __init__(self, opts: dict | None = None) -> None:
        self.opts = opts or {}
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
        except pygame.error:
            pass
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass
        try:
            pygame.joystick.init()
        except pygame.error:
            pass
        self.joysticks = self._init_joysticks()

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

        # Speicherstand laden + Grafik/Performance anwenden
        self.save_data = savemod.load()
        self.unlocked = int(self.save_data.get("unlocked", 0))
        self.audio.music_volume = float(self.save_data.get("music_volume", 0.5))
        self.audio.muted = bool(self.save_data.get("muted", False))
        self.quality = self.opts.get("quality") or self.save_data.get("quality", "smooth")
        self.fps_cap = int(self.opts.get("fps") or self.save_data.get("fps", 60))
        from .engine import controls
        self.keys = controls.load_keys(self.save_data)
        self.music_choice = self.save_data.get("music_choice") or None
        want_fs = self.opts.get("fullscreen")
        if want_fs is None:
            want_fs = self.save_data.get("fullscreen", False)
        if want_fs and not self.fullscreen:
            self._toggle_fullscreen()

        self.lives = START_LIVES
        self.level_index = 0
        self.running = True
        self.scenes = SceneManager(self)

        start_level = self.opts.get("level")
        if start_level:
            from .scenes.play import PlayScene
            self.scenes.switch(PlayScene(self, level_name=start_level))
        else:
            from .scenes.intro import IntroScene
            self.scenes.switch(IntroScene(self))

    def _init_joysticks(self):
        js = []
        try:
            for i in range(pygame.joystick.get_count()):
                j = pygame.joystick.Joystick(i)
                j.init()
                js.append(j)
        except pygame.error:
            pass
        return js

    def best_coins(self, index: int) -> int:
        return int(self.save_data.get("best_coins", {}).get(str(index), 0))

    def best_stars(self, index: int) -> int:
        return int(self.save_data.get("best_stars", {}).get(str(index), 0))

    def best_time(self, index: int) -> float:
        return float(self.save_data.get("best_time", {}).get(str(index), 0.0))

    def record_result(self, index: int, coins: int, stars: int = 0,
                      time: float | None = None) -> None:
        key = str(index)
        bc = self.save_data.setdefault("best_coins", {})
        bc[key] = max(int(bc.get(key, 0)), int(coins))
        bs = self.save_data.setdefault("best_stars", {})
        bs[key] = max(int(bs.get(key, 0)), int(stars))
        if time is not None and time > 0:
            bt = self.save_data.setdefault("best_time", {})
            prev = float(bt.get(key, 0.0))
            bt[key] = time if prev <= 0 else min(prev, time)
        self.save_progress()

    def save_progress(self) -> None:
        self.save_data["unlocked"] = self.unlocked
        self.save_data["music_volume"] = self.audio.music_volume
        self.save_data["muted"] = self.audio.muted
        self.save_data["quality"] = self.quality
        self.save_data["fps"] = self.fps_cap
        self.save_data["fullscreen"] = self.fullscreen
        self.save_data["keys"] = self.keys
        self.save_data["music_choice"] = self.music_choice
        savemod.save(self.save_data)

    def _load_audio(self) -> None:
        for name in ("jump", "coin", "stomp", "hurt", "win", "spring", "grow",
                     "checkpoint", "throw"):
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
        if (tw, th) == (VIRTUAL_W, VIRTUAL_H):
            scaled = self.screen                     # 1:1, keine Skalierung nötig
        elif self.quality == "smooth":
            scaled = pygame.transform.smoothscale(self.screen, (tw, th))
        else:                                        # "fast": nearest (Pi/schwache HW)
            scaled = pygame.transform.scale(self.screen, (tw, th))
        self.window.fill((0, 0, 0))
        self.window.blit(scaled, ((w - tw) // 2, (h - th) // 2))
        pygame.display.flip()

    def view_transform(self):
        """Skalierungsfaktor + Offset des internen Bildes im Fenster (für Maus)."""
        w, h = self.window.get_size()
        s = min(w / VIRTUAL_W, h / VIRTUAL_H)
        tw, th = VIRTUAL_W * s, VIRTUAL_H * s
        return s, (w - tw) / 2, (h - th) / 2

    def mouse_virtual(self):
        """Mausposition in interne Renderkoordinaten umrechnen."""
        mx, my = pygame.mouse.get_pos()
        s, ox, oy = self.view_transform()
        if s <= 0:
            return (0, 0)
        return ((mx - ox) / s, (my - oy) / s)

    def run(self) -> None:
        clock = pygame.time.Clock()
        acc = 0.0
        while self.running:
            acc += min(clock.tick(self.fps_cap) / 1000.0, 0.10)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self._toggle_fullscreen()
                elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self._windowed_size = (event.w, event.h)
                elif event.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                    self.joysticks = self._init_joysticks()
                    self.scenes.handle_event(event)
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
