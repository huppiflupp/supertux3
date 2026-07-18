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


def test_all_levels_load():
    from supertux3.game import Game
    from supertux3.scenes.play import PlayScene
    from supertux3.settings import LEVEL_FILES
    g = Game()
    for i in range(len(LEVEL_FILES)):
        ps = PlayScene(g, i)
        ps.on_enter()
        ps.draw(g.screen)
    pygame.quit()


def test_tmx_roundtrip(tmp_path=None):
    import json
    import tempfile
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import json_to_tmx
    from supertux3.world.tmx import parse_tmx

    root = Path(__file__).resolve().parents[1]
    data = json.load(open(root / "levels" / "level1.json", encoding="utf-8"))
    out = Path(tempfile.mkdtemp()) / "level1.tmx"
    json_to_tmx.convert(data).write(out, encoding="unicode", xml_declaration=True)
    back = parse_tmx(out)
    assert len(back["solid"]) == len(data["solid"])
    assert len(back["entities"]) == len(data["entities"])
    assert back["solid"][14] == data["solid"][14]


def test_save_roundtrip():
    import os
    import tempfile
    os.environ["XDG_DATA_HOME"] = tempfile.mkdtemp()
    from supertux3.engine import save as sv
    d = sv.load()
    d["unlocked"] = 3
    d["best_coins"]["2"] = 17
    sv.save(d)
    again = sv.load()
    assert again["unlocked"] == 3
    assert again["best_coins"]["2"] == 17


if __name__ == "__main__":
    test_assets_and_menu()
    test_level_and_physics()
    test_all_levels_load()
    test_tmx_roundtrip()
    test_save_roundtrip()
    print("Smoke-Tests OK")
