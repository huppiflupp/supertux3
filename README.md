# SuperTux3 🐧

Ein 2D-Jump'n'Run im Geiste von [SuperTux 2](https://www.supertux.org/) —
neu gebaut in **Python + pygame-ce**. Freundlicher Pinguin „Pengu", grüne
Hügelwelt, Münzen, stampfbare Schneebälle, klassisches Sprung-Gameplay.

![Titel](assets/images/background/title_art.png)

## Schnellstart

```bash
# 1. Repo holen
git clone https://github.com/huppiflupp/supertux3
cd supertux3

# 2. Spielen (legt beim 1. Start automatisch ein venv an, installiert
#    Abhängigkeiten, erzeugt fehlende Assets und startet das Spiel)
./run.sh
```

Voraussetzung: **Python 3.10+**. `run.sh` erledigt den Rest selbst.
Für schwache Hardware: `./run.sh --quality fast --fps 30` (oder im Spiel
**Optionen → Grafik = „Schnell"**).

## Fest installieren (auch für andere Rechner / Kinder)

```bash
git clone https://github.com/huppiflupp/supertux3
cd supertux3
bash packaging/install-user.sh     # ohne Root: Menüeintrag "SuperTux3" + Icon
```

Danach startet „SuperTux3" aus dem Anwendungsmenü (oder per `supertux3` im Terminal).

- **Systemweit:** `sudo make install`
- **Flatpak / RPM / DEB** und **Raspberry Pi 400**: siehe
  [docs/packaging.md](docs/packaging.md) und [docs/pi400.md](docs/pi400.md).

Zum Spielen genügt Python 3.10+ und `pygame` (empfohlen `pygame-ce`).

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

- Python 3.14 + pygame-ce, interne Auflösung 960×540, 32-px-Kacheln (SuperTux2-Stil).
- Feste-Zeitschritt-Physik, achsenweise AABB-Kachelkollision.
- Grafik: prozedurale Pixel-Art (PIL) + FLUX-Kulissen (ComfyUI/RTX 5080).
- Audio: prozedurale Chiptune-Synthese (numpy).

## Lizenz / Herkunft
Eigenständige Neuimplementierung, inspiriert von SuperTux. Kein SuperTux2-Code.
Alle Assets in diesem Repo sind generiert (Skripte unter `tools/`).
