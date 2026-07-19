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
│   │   ├── camera.py          # weiche, begrenzte Kamera + Screen-Shake
│   │   ├── animation.py       # Frame-Animation
│   │   ├── particles.py       # Partikelsystem + schwebende Texte (Juice)
│   │   ├── controls.py        # zentrale Steuerung: Tastatur + Gamepad
│   │   ├── save.py            # Speicherstand (Fortschritt, Highscores, Audio)
│   │   ├── spritesheet.py     # Bild laden + Streifen/Grid schneiden (fehlertolerant)
│   │   └── audio.py           # Musik + SFX (fehlertolerant, Lautstärke/Mute)
│   ├── world/
│   │   ├── tilemap.py         # Kachelgitter: Kollision + Darstellung
│   │   ├── tmx.py             # Tiled-TMX-Import (CSV-Layer + Objektgruppen)
│   │   └── level.py           # Levelformat/TMX + Themes -> Welt aufbauen
│   ├── entities/
│   │   ├── entity.py          # Basis: Physik + Kachel-/Plattform-Kollision
│   │   ├── player.py          # "Pengu" klein/groß, Squash/Stretch, Power-Up
│   │   ├── enemy.py           # Schneeball / Stachler (nicht stampfbar) / Flieger
│   │   ├── boss.py            # "Frostkönig" (3 Treffer) + Eis-Projektile
│   │   ├── platform.py        # MovingPlatform (mit Mitnahme), Spring, Checkpoint
│   │   └── collectible.py     # Münze, Wachstums-Item, Zielfahne
│   └── scenes/
│       ├── intro.py           # animierte Titel-Intro (überspringbar)
│       ├── menu.py            # Titelmenü (nutzt title_art.png)
│       ├── worldmap.py        # Welt-Karte (Knoten/Pfad/Avatar) – Level wählen
│       ├── options.py         # Optionen (Grafik/FPS/Vollbild/Lautstärke/Steuerung)
│       ├── keybind.py         # freie Tastenbelegung
│       ├── editor.py          # In-Game-Level-Editor (Maus+Tastatur)
│       ├── play.py            # Gameplay (Effekte, Power-Up, Sterne/Timer, Boss)
│       └── gameover.py        # Ergebnis-Szene (Level/Spiel geschafft / Game Over)
├── assets/
│   ├── images/{characters,enemies,collectibles,tiles,props,background,ui}/
│   ├── audio/{music,sfx}/
│   └── fonts/
├── levels/level1..10.json     # 10 Level (per tools/build_levels.py erzeugt)
├── tools/
│   ├── asset_pipeline/
│   │   ├── gen_pixelart.py     # HD-Sprites/Kacheln/Props/Boss (PIL, supersampled)
│   │   ├── gen_audio.py        # Musik (level1/2/ice/title) + SFX (numpy)
│   │   └── comfy_gen.py        # FLUX-Hintergründe via ComfyUI-API (stdlib)
│   ├── build_levels.py         # baut levels/level1..10.json deterministisch
│   └── json_to_tmx.py          # exportiert ein JSON-Level nach Tiled-TMX
├── docs/
│   ├── PLAN.md                 # Fahrplan / Vision / Roadmap
│   └── asset_pipeline.md       # ComfyUI/FLUX-Setup & Nutzung
└── tests/test_smoke.py
```

### Mechaniken (M2)
- **Power-Up klein/groß**: Wachstums-Item macht Pengu groß; Treffer verkleinert
  statt sofort Leben zu kosten (`Player.take_hit()` → `die`/`shrink`/`none`).
- **Gegner**: Schneeball (stampfbar), Flieger (Sinus-Flug, stampfbar), Stachler
  (`stompable=False` → Kontakt verletzt immer).
- **Plattformen/Federn/Checkpoints**: bewegliche Plattformen tragen den Spieler
  (Ride-Logik in `play.py::_recompute_ride`), Federn katapultieren, Checkpoints
  verschieben den Respawn-Punkt.
- **Juice**: `engine/particles.py` (Münz-Funken, Stampf-Staub, Sprung/Landung,
  Tod-Poof, Sparkle, schwebende Punkte) + Kamera-Shake + Squash/Stretch.
- **Progression**: `settings.LEVEL_FILES`, `game.unlocked`; Ziel → nächstes Level.
- **Pause** (P/ESC) mit Lautstärke (`+`/`-`), Neustart (R), Level-Auswahl (Q).

### Mechaniken (M3)
- **Speichern/Highscores**: `engine/save.py` (XDG-Datenverzeichnis
  `~/.local/share/supertux3/save.json`); `game.unlocked`, `best_coins` je Level,
  Lautstärke/Mute. `game.record_result()` / `game.save_progress()`.
- **Gamepad**: `engine/controls.py` übersetzt Tastatur + Joystick in Menü-Aktionen;
  der Spieler liest Stick/D-Pad/A-Button direkt. Automatisches Erkennen beim
  Ein-/Ausstecken.
- **Boss „Frostkönig"** (`entities/boss.py`): 3 Stampf-Treffer, wird schneller,
  wirft Eis-Projektile; Boss-Level 10, Sieg = Spiel durchgespielt.
- **Tiled-Import**: `world/tmx.py` lädt `.tmx` (CSV-Layer + Objektgruppen
  `entities`/`props`); `tools/json_to_tmx.py` exportiert (verlustfreier Round-Trip).
  Konvention: firstgid=1, GID N == Spiel-Kachel-ID N.
- **10 Level** über 5 Themes; `Level.load()` erkennt `.json` und `.tmx`.

### Mechaniken (M4)
- **8-bit-Musik neu** (`tools/asset_pipeline/gen_audio.py`): Vibrato, Arpeggien,
  Rausch-Drums, ADSR; 7 Tracks (title/level1-3/ice/cave/**boss**). Theme→Track in
  `world/level.py::THEMES`; Boss-Level setzen `"music":"boss.ogg"`.
- **Sterne + Bestzeit**: `Star` (3/Level, `tools/build_levels.py::sprinkle_stars`),
  Timer im HUD; `game.record_result(idx, coins, stars, time)` → `best_stars`/
  `best_time`; Anzeige in der Level-Auswahl.
- **Zweiter Boss** „Schattenkönig": `Boss(..., variant="shadow")` (lila getönt,
  4 HP, schneller). Level-Format: `["boss", tx, ty, "shadow"]`.
- **In-Game-Editor** (`scenes/editor.py`): Cursor-basiert, setzt Kacheln/Entities/
  Props, Startpunkt (B), Theme (Y), speichert nach `levels/<datei>` (F5), Test (P).
  Custom-Level via `PlayScene(game, level_name=...)`. Zugang: Menü/Level-Auswahl `E`.
- **Intro** (`scenes/intro.py`): Spielstart zeigt Intro → Menü.
- **15 Level** gesamt (2 Bosse).

### Mechaniken (M5) — Distribution & Feinschliff
- **Optionen/Performance**: `scenes/options.py`; `game.quality` ("smooth"/"fast"),
  `game.fps_cap`; `_present()` wählt smoothscale vs nearest. ARM-Autoprofil in
  `settings` (`IS_ARM`, `DEFAULT_QUALITY`). CLI in `main.py`
  (`--quality/--fps/--fullscreen/--level`). Alles im Speicherstand.
- **Maus-Editor**: `scenes/editor.py` mit freier Kamera + `game.mouse_virtual()`
  (Fenster→interne Koordinaten). Custom-Level in `settings.USER_LEVEL_DIR`
  (`~/.local/share/supertux3/levels`); `Level.load()` sucht dort zusätzlich.
- **Datenpfade**: `settings._find_root()` findet `assets/`+`levels/` im Dev-Baum
  ODER in `<prefix>/share/supertux3` (Install) ODER via `SUPERTUX3_DATA`.
- **Paketierung** (`packaging/`, `Makefile`, `pyproject.toml`): `make install`,
  Nutzer-Installer `install-user.sh`, Flatpak/RPM/DEB, Desktop-Eintrag + Icon
  (`tools/asset_pipeline/gen_icon.py`). Siehe `docs/packaging.md`.
- **Raspberry Pi 400**: `docs/pi400.md` (Python 3.11, `--quality fast`, KMSDRM).

### Mechaniken (M6) — Welt-Karte & Steuerung
- **Welt-Karte** (`scenes/worldmap.py`): scrollende Knotenkarte statt Liste;
  `THEME_LOOK` färbt Knoten/Hintergrund je Welt; Avatar hüpft auf dem gewählten
  Knoten; Sperre = `sel <= game.unlocked`. Menü/Pause(Q)/Ergebnis führen hierher,
  und `PlayScene._next_level` kehrt nach jedem Level zur Karte zurück.
- **Freie Tastenbelegung** (`engine/controls.py`: `ACTIONS`, `DEFAULT_KEYS`,
  `load_keys`, `key_label`): `game.keys` wird aus dem Speicherstand gebaut; der
  Spieler liest daraus (`player.update`). `scenes/keybind.py` belegt Tasten neu
  (Optionen → Steuerung). Menü-Navigation bleibt fest (Pfeile/Enter/ESC + Gamepad).

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
  Vorhandene Kulissen: `sky_parallax`, `sunset_hills`, `night_hills`,
  `ice_mountains`, `cave` (+ `title_art`). Level-Theme → Hintergrund/Musik in
  `world/level.py::THEMES`.
  **Wichtig:** ComfyUI nach dem Generieren beenden, damit die GPU (RTX 5080)
  wieder frei ist: `pkill -f "main.py --listen"`.

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
