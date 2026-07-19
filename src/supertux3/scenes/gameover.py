"""Ergebnis-Szene: gewonnen oder verloren."""
from __future__ import annotations

import pygame

from ..engine.scene import Scene
from ..settings import VIRTUAL_W, VIRTUAL_H, WHITE, UI_SHADOW, START_LIVES


class ResultScene(Scene):
    def __init__(self, game, won: bool, coins: int, total: int, game_complete: bool = False):
        super().__init__(game)
        self.won = won
        self.coins = coins
        self.total = total
        self.game_complete = game_complete

    def on_enter(self) -> None:
        self.big = pygame.font.Font(None, 100)
        self.font = pygame.font.Font(None, 42)
        if self.won:
            self.game.audio.play_music("title.ogg")
        else:
            self.game.audio.stop_music()

    def handle_event(self, event: pygame.event.Event) -> None:
        from ..engine.controls import nav
        if nav(event) in ("confirm", "back"):
            from .worldmap import WorldMapScene
            self.game.lives = START_LIVES
            self.game.scenes.switch(WorldMapScene(self.game))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((24, 34, 58) if not self.won else (32, 64, 40))
        if self.game_complete:
            title = "Alle Level geschafft!"
        else:
            title = "Level geschafft!" if self.won else "Game Over"
        color = (255, 240, 120) if self.won else (255, 120, 120)
        self._center(surface, title, self.big, color, VIRTUAL_H // 2 - 40)
        self._center(surface, f"Münzen: {self.coins} / {self.total}",
                     self.font, WHITE, VIRTUAL_H // 2 + 30)
        self._center(surface, "ENTER / ESC = Level-Auswahl",
                     self.font, (210, 220, 240), VIRTUAL_H // 2 + 78)

    def _center(self, surface, text, font, color, y) -> None:
        img = font.render(text, True, color)
        rect = img.get_rect(center=(VIRTUAL_W // 2, y))
        surface.blit(font.render(text, True, UI_SHADOW), rect.move(3, 3))
        surface.blit(img, rect)


# Rückwärtskompatibler Alias
GameOverScene = ResultScene
