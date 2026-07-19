"""Einstiegspunkt für SuperTux3."""
from __future__ import annotations

import argparse


def main() -> None:
    ap = argparse.ArgumentParser(prog="supertux3",
                                 description="SuperTux3 – ein 2D-Jump'n'Run")
    ap.add_argument("--quality", choices=["smooth", "fast"],
                    help="Grafik: smooth (Desktop) oder fast (Pi/schwache HW)")
    ap.add_argument("--fps", type=int, choices=[30, 60], help="Bildrate")
    ap.add_argument("--fullscreen", dest="fullscreen", action="store_true", default=None)
    ap.add_argument("--windowed", dest="fullscreen", action="store_false")
    ap.add_argument("--level", help="Leveldatei direkt starten (z.B. level1.json)")
    args = ap.parse_args()
    opts = {k: v for k, v in vars(args).items() if v is not None}

    from .game import Game
    Game(opts).run()


if __name__ == "__main__":
    main()
