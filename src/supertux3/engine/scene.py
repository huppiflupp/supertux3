"""Szenen-Basisklasse und ein einfacher Szenen-Stack."""
from __future__ import annotations

import pygame


class Scene:
    """Basisklasse. Szenen bekommen eine Referenz auf das Game-Objekt."""

    def __init__(self, game) -> None:
        self.game = game

    def handle_event(self, event: pygame.event.Event) -> None:  # noqa: D401
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass


class SceneManager:
    """Hält die aktive Szene und wechselt weich zwischen ihnen."""

    def __init__(self, game) -> None:
        self.game = game
        self.current: Scene | None = None

    def switch(self, scene: Scene) -> None:
        if self.current is not None:
            self.current.on_exit()
        self.current = scene
        self.current.on_enter()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.current:
            self.current.handle_event(event)

    def update(self, dt: float) -> None:
        if self.current:
            self.current.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        if self.current:
            self.current.draw(surface)
