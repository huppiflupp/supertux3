"""Headless-Smoke-Tests: Laden, Physik, Rendern ohne Fenster/Audio.

Aufruf:  PYTHONPATH=src .venv/bin/python -m pytest tests/    (oder direkt ausführen)
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame  # noqa: E402


def _game():
    from supertux3.game import Game
    return Game()


def test_assets_and_menu():
    g = _game()
    assert g.assets.tileset, "Kachelsatz fehlt"
    assert g.assets.player["walk"], "Spieler-Frames fehlen"
    g.scenes.update(0.1)
    g.scenes.draw(g.screen)   # darf nicht werfen
    pygame.quit()


def test_level_and_physics():
    from supertux3.game import Game
    from supertux3.scenes.play import PlayScene
    from supertux3.settings import FIXED_DT

    class Keys:
        def __getitem__(self, k):
            return k == pygame.K_RIGHT
    pygame.key.get_pressed = lambda: Keys()

    g = Game()
    play = PlayScene(g)
    g.scenes.switch(play)
    p = play.level.player
    start_x = p.x
    for _ in range(120):
        play.update(FIXED_DT)
        play.draw(g.screen)
    assert p.x > start_x, "Spieler bewegt sich nicht nach rechts"
    assert p.y < play.level.height_px, "Spieler durch den Boden gefallen"
    assert play.level.total_coins > 0
    pygame.quit()


if __name__ == "__main__":
    test_assets_and_menu()
    test_level_and_physics()
    print("Smoke-Tests OK")
