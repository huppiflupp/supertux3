"""Audio-Verwaltung: Hintergrundmusik + Soundeffekte.

Fehlertolerant: Ist kein Audiogerät verfügbar oder fehlen Dateien, läuft das
Spiel stumm weiter, statt abzustürzen.
"""
from __future__ import annotations

from pathlib import Path

import pygame

from ..settings import AUDIO_DIR


class AudioManager:
    def __init__(self) -> None:
        self.ok = pygame.mixer.get_init() is not None
        self.sfx: dict[str, pygame.mixer.Sound] = {}
        self.music_volume = 0.5
        self.sfx_volume = 0.6
        self.muted = False
        self._current_music: str | None = None

    def load_sfx(self, name: str, filename: str) -> None:
        if not self.ok:
            return
        path = AUDIO_DIR / "sfx" / filename
        if not path.exists():
            return
        try:
            snd = pygame.mixer.Sound(str(path))
            snd.set_volume(self.sfx_volume)
            self.sfx[name] = snd
        except pygame.error:
            pass

    def play(self, name: str) -> None:
        if not self.ok or self.muted:
            return
        snd = self.sfx.get(name)
        if snd is not None:
            snd.play()

    def play_music(self, filename: str, loop: bool = True) -> None:
        if not self.ok:
            return
        path = AUDIO_DIR / "music" / filename
        if not path.exists() or self._current_music == filename:
            return
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(0.0 if self.muted else self.music_volume)
            pygame.mixer.music.play(-1 if loop else 0)
            self._current_music = filename
        except pygame.error:
            pass

    def stop_music(self) -> None:
        if self.ok:
            pygame.mixer.music.stop()
            self._current_music = None

    def toggle_mute(self) -> None:
        self.muted = not self.muted
        if self.ok:
            pygame.mixer.music.set_volume(0.0 if self.muted else self.music_volume)
