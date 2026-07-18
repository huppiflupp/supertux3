#!/usr/bin/env bash
# SuperTux3 starten. Legt bei Bedarf venv an, installiert Abhängigkeiten und
# generiert fehlende Assets, dann startet das Spiel.
set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    echo "[SuperTux3] Erstelle venv ..."
    python3 -m venv .venv
    .venv/bin/pip install -q --upgrade pip
    .venv/bin/pip install -q -r requirements.txt
fi

# Assets bei Bedarf erzeugen (prozedural, offline)
[ -f assets/images/characters/pengu.png ] || .venv/bin/python tools/asset_pipeline/gen_pixelart.py
[ -f assets/audio/music/level1.ogg ]      || .venv/bin/python tools/asset_pipeline/gen_audio.py
[ -f levels/level1.json ]                  || .venv/bin/python tools/build_level1.py

exec env PYTHONPATH=src .venv/bin/python -m supertux3 "$@"
