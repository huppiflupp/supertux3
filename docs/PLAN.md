# SuperTux3 — Plan & Roadmap

## Vision
Ein eigenständiges 2D-Jump'n'Run im Geiste von **SuperTux 2**: freundlicher
Pinguin-Held, grüne Hügelwelt, Münzen, stampfbare Gegner, klassisches
Sprung-Gameplay. Umgesetzt in Python/pygame-ce — schlank, erweiterbar,
vollständig reproduzierbare Assets, optional KI-generierte Kulissen auf lokaler
GPU.

Warum kein direkter SuperTux2-Fork? SuperTux2 ist ein großes C++/SDL/Squirrel-
Projekt. Ein Port/Build hätte den Weg zu einem *spielbaren* Prototyp um Wochen
verlängert. Wir übernehmen die **Ideen** (Tilemaps, Stampf-Gegner, Sammel-Münzen,
Parallax, Zielobjekt), nicht den Code.

## Meilensteine

### M0 — Fundament ✅
- [x] Projektstruktur, venv, pygame-ce auf Python 3.14 verifiziert
- [x] Feste-Zeitschritt-Hauptschleife, Szenen-Manager
- [x] Kachel-Kollision (achsenweise AABB), Kamera

### M1 — Spielbarer Prototyp ✅ (dieser Stand)
- [x] Spieler „Pengu": Laufen, variabler Sprung, Coyote-Time, Jump-Buffer, Ducken
- [x] Gegner „Schneeball": Laufen, Umdrehen an Wand/Abgrund, Stampfen
- [x] Münzen, Zielfahne, Leben, Tod/Respawn, Level-Ende
- [x] Titelmenü, Ergebnis-Szene
- [x] Prozedurale Pixel-Art (Sprites, Kacheln, Props)
- [x] Prozedurale Musik (Level + Titel) und SFX
- [x] FLUX-Hintergründe + Titelbild (ComfyUI, lokale RTX 5080)
- [x] Level 1 „Grüne Hügel 1", Headless-Smoke-Tests

### M2 — Mehr Spiel ✅
- [x] 6 Level + Level-Auswahl mit Fortschritt; 5 Themes (Gras/Sonnenuntergang/
      Nacht/Eis/Höhle) mit eigenen FLUX-Kulissen und Musik
- [x] Power-Up-Zustände (klein/groß; Treffer verkleinert statt Leben zu kosten)
- [x] 2 neue Gegnertypen: Flieger (Sinus-Flug) und Stachler (nicht stampfbar)
- [x] Bewegliche Plattformen (mit Mitnahme), Sprungfedern, Checkpoints
- [x] Partikel & „Juice": Funken/Staub/Poof/Sparkle, schwebende Punkte,
      Screen-Shake, Squash/Stretch
- [x] Pause-Menü mit Lautstärke, Neustart, Level-Auswahl

### M3 — Ausbau ✅
- [x] **Tiled-TMX-Import** (`world/tmx.py`) + JSON→TMX-Export (`tools/json_to_tmx.py`),
      verlustfreier Round-Trip
- [x] 10 Level über 5 Themes (Gras/Sonnenuntergang/Nacht/Eis/Höhle) inkl.
      eigener FLUX-Kulissen
- [x] Speichern/Fortschritt + Highscores (Bestmünzen je Level, `engine/save.py`,
      XDG-Datenverzeichnis)
- [x] Gamepad-Unterstützung (`engine/controls.py`: Stick/D-Pad/Buttons, Menüs)
- [x] Boss am Weltende: „Frostkönig" (3 Treffer, Eis-Projektile, Boss-Level 10)

### M4 — Ausbau ✅
- [x] **In-Game-Level-Editor** (`scenes/editor.py`): Kacheln/Entities/Props
      setzen/löschen, Theme/Startpunkt, Speichern (F5) + Testspielen (P)
- [x] **Zweiter Boss** „Schattenkönig" (Variante, 4 HP, schneller) + 5 neue
      Level → **15 Level** gesamt über 5 Themes
- [x] **Sammel-Sterne** (3/Level) + **Bestzeiten**; Anzeige in Level-Auswahl
- [x] **Bessere 8-bit-Musik**: Synth-Rewrite (Vibrato, Arpeggien, Drums, ADSR),
      7 eigenständige Tracks inkl. treibendem Boss-Theme
- [x] **Intro-Sequenz** vor dem Menü (animiert, überspringbar)

### M5 — Distribution & Feinschliff ✅
- [x] **Optionsmenü** (`scenes/options.py`): Grafik, Bildrate, Vollbild,
      Lautstärke, Ton – persistent im Speicherstand
- [x] **Grafik-/Performance-Modi**: „schnell" (nearest) vs „glatt" (smooth),
      FPS 30/60; ARM-Autoprofil; CLI `--quality/--fps/--fullscreen/--level`
- [x] **Maus-Editor** + freie Kamera; Custom-Level in schreibbarem
      User-Verzeichnis (auch bei read-only Installation)
- [x] **Paketierung**: pyproject, Makefile-Install, Launcher, Desktop-Eintrag,
      App-Icon, AppStream-Metainfo, **Flatpak/RPM/DEB**, Nutzer-Installer
- [x] **Raspberry-Pi-400-Port**: Python-3.11-tauglich, ARM-Erkennung,
      KMSDRM/Perf-Doku (`docs/pi400.md`)

### M6 — Welt-Karte & Steuerung ✅
- [x] **Welt-Karte** (`scenes/worldmap.py`): scrollende Knotenkarte über 5 Welten,
      Pengu-Avatar, farbige Level-Knoten, Sterne/Sperren, Pfad; ersetzt die Liste.
      Nach jedem Level zurück zur Karte (Fortschritt sichtbar).
- [x] **Freie Tastenbelegung** (`scenes/keybind.py`, `engine/controls.py`):
      Links/Rechts/Springen/Ducken frei belegbar, persistent; Standard-Reset;
      Zugang über Optionen → Steuerung.

### M7 — Welten, Buddies, Dynamik ✅
- [x] Neue Welten **Ägypten**, **Weltraum**, **Großstadt** (je 3 Level, eigene
      Kacheln/Props/Gegner/Musik) → **24 Level / 8 Welten**
- [x] Animierte Super-Mario-Weltkarte mit Themen-Kulissen + Teasern
- [x] Buddy-System: **Schildkröte** (Schild), **Giraffe** (Brücke),
      **kämpfender Freund** (wirft Fische)
- [x] Neue Powerups: Fisch-Wurf, Fischregen; zerstörbare Loot-Boxen;
      schießender Gegner (Feuerblume)
- [x] Dynamik: **Wetter** (Regen/Schnee/Nebel) + **Wind-Physik**
- [x] **Schrägen** im Tileset (45°) mit Auto-Step
- [x] **Geheimlevel** über versteckten Ausgang
- [x] Pinguin-Rework (Flossen), HUD-Piktogramme, Musikauswahl

### M8 — Ideen (offen)
- [ ] **ComfyUI/Blender-Prerender** von Held/Deko + abgeleitete Animation
      (sobald die GPU frei ist — vor jedem Lauf `nvidia-smi` prüfen!)
- [ ] Story-Cutscenes zwischen Welten; abzweigende Kartenpfade; Welt-2-Boss
- [ ] Mehr Boss-Typen; Zeitangriff-Modus; Online-Bestenliste
- [ ] Vollständig offline-reproduzierbarer Flatpak (vendored Wheels)

## Asset-Strategie
- **Spielfertige Sprites** (Held, Gegner, Kacheln, Münzen): prozedural (PIL),
  weil Diffusion keine konsistenten Animations-Frames mit sauberem Alpha liefert.
- **Kulissen/Titel/Promo**: FLUX-schnell über ComfyUI (dort ist Diffusion stark).
- **Musik/SFX**: prozedurale Chiptune-Synthese (numpy), offline & deterministisch.
- Alles über `tools/` **reproduzierbar** — Assets sind Ausgabe, nicht Quelle.

## Technische Leitplanken
- Physik in Pixel/s, **fester Zeitschritt** 1/60 s.
- Interne Auflösung 960×540 (Kachel 32px), seitenverhältnistreu aufs Fenster skaliert.
- HD-Grafik supersampled (4×) gezeichnet und geglättet — SuperTux2-orientiert.
- Konstanten zentral in `settings.py`.
- Fehlertolerant: fehlende Assets/kein Audiogerät dürfen nicht crashen.
