# SuperTux3 🐧

Ein 2D-Jump'n'Run im Geiste von [SuperTux 2](https://www.supertux.org/) —
neu gebaut in **Python + pygame-ce**. Freundlicher Pinguin „Pengu", grüne
Hügelwelt, Münzen, stampfbare Schneebälle, klassisches Sprung-Gameplay.

![Titel](assets/images/background/title_art.png)

## Spielen

```bash
./run.sh
```

Das Skript legt beim ersten Start ein venv an, installiert die Abhängigkeiten,
erzeugt fehlende Assets und startet das Spiel.

## Steuerung

| Taste | Aktion |
|-------|--------|
| ← → / A D | bewegen |
| Leertaste / W / ↑ | springen (variabel — länger gedrückt = höher) |
| ↓ / S | ducken |
| auf Gegner springen | stampfen |
| R | Level neu starten |
| M | Ton an/aus |
| F11 | Vollbild |
| ESC | Menü / Beenden |

## Aufbau

Alles Wesentliche steht in **[CLAUDE.md](CLAUDE.md)** (Architektur, Struktur,
Erweiterung) und **[docs/PLAN.md](docs/PLAN.md)** (Roadmap). Assets werden
prozedural bzw. per lokaler FLUX-Pipeline erzeugt — siehe
[docs/asset_pipeline.md](docs/asset_pipeline.md).

## Technik

- Python 3.14 + pygame-ce, interne Auflösung 480×270 (Pixel-Look).
- Feste-Zeitschritt-Physik, achsenweise AABB-Kachelkollision.
- Grafik: prozedurale Pixel-Art (PIL) + FLUX-Kulissen (ComfyUI/RTX 5080).
- Audio: prozedurale Chiptune-Synthese (numpy).

## Lizenz / Herkunft
Eigenständige Neuimplementierung, inspiriert von SuperTux. Kein SuperTux2-Code.
Alle Assets in diesem Repo sind generiert (Skripte unter `tools/`).
