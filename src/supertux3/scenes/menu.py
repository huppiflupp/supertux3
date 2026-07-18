"""Titelmenü."""
from __future__ import annotations

import pygame

from ..engine.scene import Scene
from ..engine.spritesheet import load_image
from ..settings import VIRTUAL_W, VIRTUAL_H, IMAGE_DIR, WHITE, UI_SHADOW, GAME_TITLE, START_LIVES


class MenuScene(Scene):
    def on_enter(self) -> None:
        self.title_font = pygame.font.Font(None, 130)
        self.font = pygame.font.Font(None, 42)
        self.t = 0.0
        art = IMAGE_DIR / "background" / "title_art.png"
        self.art = None
        if art.exists():
            img = load_image(art)
            scale = max(VIRTUAL_W / img.get_width(), VIRTUAL_H / img.get_height())
            self.art = pygame.transform.smoothscale(
                img, (int(img.get_width() * scale), int(img.get_height() * scale)))
        self.game.audio.play_music("title.ogg")

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                from .play import PlayScene
                self.game.lives = START_LIVES
                self.game.scenes.switch(PlayScene(self.game))
            elif event.key == pygame.K_ESCAPE:
                self.game.running = False
            elif event.key == pygame.K_m:
                self.game.audio.toggle_mute()

    def update(self, dt: float) -> None:
        self.t += dt

    def draw(self, surface: pygame.Surface) -> None:
        if self.art is not None:
            rect = self.art.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2))
            surface.blit(self.art, rect)
            veil = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
            veil.fill((10, 20, 40, 70))
            surface.blit(veil, (0, 0))
        else:
            surface.fill((92, 148, 252))

        self._center(surface, GAME_TITLE, self.title_font, (255, 240, 120), int(VIRTUAL_H * 0.30))
        if int(self.t * 2) % 2 == 0:
            self._center(surface, "ENTER = Spielen", self.font, WHITE, VIRTUAL_H - 130)
        self._center(surface, "Pfeile/WASD  bewegen   ·   Leertaste springen",
                     self.font, (220, 230, 245), VIRTUAL_H - 84)
        self._center(surface, "M = Ton   ·   ESC = Beenden",
                     self.font, (200, 210, 230), VIRTUAL_H - 48)

    def _center(self, surface, text, font, color, y) -> None:
        img = font.render(text, True, color)
        rect = img.get_rect(center=(VIRTUAL_W // 2, y))
        surface.blit(font.render(text, True, UI_SHADOW), rect.move(3, 3))
        surface.blit(img, rect)
