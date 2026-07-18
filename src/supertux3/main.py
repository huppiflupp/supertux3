"""Einstiegspunkt für SuperTux3."""
from __future__ import annotations


def main() -> None:
    from .game import Game
    Game().run()


if __name__ == "__main__":
    main()
