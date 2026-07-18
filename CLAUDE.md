# SuperTux3 — Projektdokumentation (CLAUDE.md)

Ein 2D-Jump'n'Run im Geiste von **SuperTux 2**, neu in **Python + pygame-ce**
umgesetzt. Ziel: eigenständiges, erweiterbares Spiel mit sauberer Architektur,
prozedural erzeugten Grafiken/Sounds und optional KI-generierten Hintergründen
(ComfyUI/FLUX auf lokaler RTX 5080).

> Dieses Dokument ist die zentrale Referenz für zukünftige Sitzungen. Es
> beschreibt *warum* Dinge so sind, nicht nur *was* da ist.

---

## 1. Schnellstart

```bash
./run.sh                 # legt venv an, erzeugt fehlende Assets, startet das Spiel
```

Manuell:
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python tools/asset_pipeline/gen_pixelart.py     # Sprites/Kacheln
python tools/asset_pipeline/gen_audio.py        # Musik + SFX
python tools/build_level1.py                    # Level 1
PYTHONPATH=src python -m supertux3
```

**Steuerung:** Pfeiltasten/WASD = bewegen · Leertaste/W/↑ = springen ·
↓/S = ducken · Gegner von oben = stampfen · `R` = Level neu · `M` = Ton an/aus ·
`F11` = Vollbild · `ESC` = Menü/Beenden.

**Tests:** `PYTHONPATH=src .venv/bin/python tests/test_smoke.py`

---

## 2. Technische Entscheidungen (Kontext)

| Thema | Entscheidung | Warum |
|------|--------------|-------|
| Sprache/Engine | Python 3.14 + **pygame-ce 2.5.7** | Schnellster Weg zu einem spielbaren Prototyp; SuperTux2 ist C++/SDL und wäre ein Wochen-Port. pygame-ce hat native cp314-Wheels. |
| Renderauflösung | intern **960×540** (Kachel 32px, wie SuperTux2), seitenverhältnistreu aufs Fenster skaliert | „Gute Grafik" bei gleichem Sichtfeld (30 Kacheln). Physik skaliert mit → Spielgefühl identisch zum 16px-Prototyp. |
| Grafik-Detailgrad | HD, **supersampled** (4× gezeichnet, LANCZOS herunter) | Weiche, schattierte Cartoon-Sprites statt harter Pixel — SuperTux2-orientiert. |
| Physik | **fester Zeitschritt** (1/60 s), Achsen-getrennte AABB-Kollision | Deterministisches Spielgefühl auf jeder Hardware. |
| Spielfigur-Grafik | **prozedurale Pixel-Art** (PIL), nicht Stable Diffusion | SD/FLUX liefert keine konsistenten, spielfertigen Animations-Frames mit Alpha; prozedural = konsistent, klein, versionierbar. |
| Hintergründe/Titel | **ComfyUI + FLUX-schnell** (lokale RTX 5080) | Dort ist Diffusion stark: weiche, stimmungsvolle Kulissen. Weicher BG + scharfer Pixel-Vordergrund = klassischer Parallax-Look. |
| Musik | **prozedurale Chiptune-Synthese** (numpy→OGG) | Offline, zuverlässig, passend zum Retro-Genre, keine Modell-Downloads. |

---

## 3. Verzeichnisstruktur

```
supertux3/
├── run.sh                     # Launcher (venv + Assets + Start)
├── requirements.txt
├── CLAUDE.md                  # dieses Dokument
├── README.md
├── src/supertux3/            # Spielcode (Paket)
│   ├── settings.py            # ALLE Konstanten (Physik, Größen, Pfade, Farben)
│   ├── game.py                # Fenster + Hauptschleife (fester Zeitschritt)
│   ├── main.py / __main__.py  # Einstiegspunkte  (python -m supertux3)
│   ├── assets.py              # zentrales Laden aller Grafiken (+ Frame-Spezifikation!)
│   ├── engine/
│   │   ├── scene.py           # Scene-Basisklasse + SceneManager
│   │   ├── camera.py          # weiche, begrenzte Kamera
│   │   ├── animation.py       # Frame-Animation
│   │   ├── spritesheet.py     # Bild laden + Streifen/Grid schneiden (fehlertolerant)
│   │   └── audio.py           # Musik + SFX (fehlertolerant, stumm ohne Gerät)
│   ├── world/
│   │   ├── tilemap.py         # Kachelgitter: Kollision + Darstellung
│   │   └── level.py           # Levelformat laden -> Welt aufbauen
│   ├── entities/
│   │   ├── entity.py          # Basis: Physik + Kachelkollision
│   │   ├── player.py          # "Pengu" (Coyote-Time, Jump-Buffer, variabler Sprung)
│   │   ├── enemy.py           # "Schneeball" (läuft, dreht um, stampfbar)
│   │   └── collectible.py     # Münze, Zielfahne
│   └── scenes/
│       ├── menu.py            # Titelmenü (nutzt title_art.png)
│       ├── play.py            # Gameplay (Kollisionen, Parallax, HUD)
│       └── gameover.py        # Ergebnis-Szene (gewonnen/verloren)
├── assets/
│   ├── images/{characters,enemies,collectibles,tiles,props,background,ui}/
│   ├── audio/{music,sfx}/
│   └── fonts/
├── levels/level1.json         # erstes Level (per tools/build_level1.py erzeugt)
├── tools/
│   ├── asset_pipeline/
│   │   ├── gen_pixelart.py     # Sprites/Kacheln/Props (PIL)
│   │   ├── gen_audio.py        # Musik + SFX (numpy)
│   │   └── comfy_gen.py        # FLUX-Hintergründe via ComfyUI-API (stdlib)
│   └── build_level1.py         # baut levels/level1.json deterministisch
├── docs/
│   ├── PLAN.md                 # Fahrplan / Vision / Roadmap
│   └── asset_pipeline.md       # ComfyUI/FLUX-Setup & Nutzung
└── tests/test_smoke.py
```

---

## 4. Architektur-Überblick

- **`Game`** hält Fenster, `Assets`, `AudioManager` und einen `SceneManager`.
  Die Hauptschleife integriert die Physik mit **festem Zeitschritt** und zeichnet
  danach einmal pro Frame.
- **Szenen** (`Menu → Play → Result`) kapseln je einen Spielzustand. Wechsel über
  `game.scenes.switch(NeueSzene(game))`.
- **Welt**: `Level` liest JSON, baut eine `Tilemap` (Kollisionsgitter) und die
  Entities (`Player`, `Snowball`, `Coin`, `Goal`) sowie Dekor-Props auf.
- **Entities** erben von `Entity` und nutzen `move_and_collide()` für achsenweise
  AABB-Kollision gegen feste Kacheln.
- **Kollision Spieler↔Welt** liegt in `PlayScene._collisions()` (Münzen sammeln,
  Gegner stampfen/Schaden, Ziel erreichen).

### Koordinaten-Konvention (wichtig!)
Levelkoordinaten sind **Kachel-Indizes**. Boden liegt auf Reihe 15 (Gras) / 16
(Erde). Etwas, das „auf dem Boden steht", bekommt `ty = 14` (die Kachel darüber).
`spawn`/Entities/Props werden unten-bündig auf `(ty+1)*TILE` gesetzt.

---

## 5. Assets erzeugen / anpassen

Alle Assets sind **reproduzierbar** — nichts ist „von Hand gemalt".

- **Pixel-Art:** `tools/asset_pipeline/gen_pixelart.py`. Die Frame-Maße dort
  müssen exakt zu `src/supertux3/assets.py` passen (Spezifikation oben in beiden
  Dateien dokumentiert): `pengu` 40×48 (9 Frames), `coin` 24×24 (6), `snowball`
  36×32 (3), Kachelsatz 32×32 (7 Kacheln, ID 0 = leer). Gezeichnet wird
  supersampled (4×) und geglättet heruntergerechnet (`Pen`-Klasse).
- **Audio:** `tools/asset_pipeline/gen_audio.py` (numpy-Synthese; OGG-Export via
  ffmpeg, SFX als WAV).
- **FLUX-Hintergründe:** siehe `docs/asset_pipeline.md`. ComfyUI liegt unter
  `~/MU/mu_generator/ComfyUI` (Python-3.11-venv, torch cu128, RTX 5080). Neues
  Bild z.B.:
  ```bash
  # ComfyUI muss laufen:  ~/MU/mu_generator/ComfyUI/run.sh
  python tools/asset_pipeline/comfy_gen.py \
      --prompt "cheerful 16-bit platformer sky, soft clouds, green hills, no text" \
      --out sky_parallax.png --width 1536 --height 768
  ```

---

## 6. Neues hinzufügen — Kochrezepte

**Neues Level:** `levels/levelN.json` anlegen (Format siehe `world/level.py`
Docstring). Kachelzeichen: `.`=leer `G`=Gras `D`=Erde `B`=Ziegel `#`=Hartblock
`S`=Stein `I`=Eis. Am einfachsten ein Build-Skript analog `tools/build_level1.py`.
Starten mit `PlayScene(game, "levelN.json")`.

**Neuer Gegner:** Klasse in `entities/` von `Entity` ableiten, `update()` +
`draw()` implementieren, in `world/level.py` beim Entity-Parsing registrieren,
Sprite im Pixel-Art-Generator ergänzen und in `assets.py` laden.

**Neue Kachel:** ID in `world/tilemap.py` (`CHAR_TO_TILE`, ggf. `SOLID_IDS`)
ergänzen, Kachelgrafik in `gen_pixelart.py::gen_tileset()` an derselben Index-
Position zeichnen.

---

## 7. Bekannte Grenzen / Roadmap

Siehe `docs/PLAN.md`. Kurz:
- Aktuell 1 Level, 1 Gegnertyp, Held ohne Power-Up-Zustände.
- Keine beweglichen Plattformen/Schrägen, kein Speichern, kein Level-Select.
- Nächste sinnvolle Schritte: mehr Level + Level-Auswahl, 2. Gegnertyp,
  Power-Ups (groß/klein wie SuperTux), bewegliche Plattformen, Partikel/Feedback,
  Tiled-Import als Level-Editor.

---

## 8. Gotchas

- **Python 3.14** ist Systemstandard; für torch/ComfyUI gibt es dafür **keine**
  Wheels → ComfyUI nutzt ein eigenes **Python-3.11**-venv. Das Spiel selbst läuft
  problemlos auf 3.14.
- `pygame.key.get_pressed()` liest echte Tastatur — in Tests per Monkeypatch
  faken (siehe `tests/test_smoke.py`).
- Headless (`SDL_VIDEODRIVER=dummy`) warnt „no fast renderer available" — harmlos.
- Assets sind **git-getrackt**, aber jederzeit über die tools/ neu erzeugbar.
