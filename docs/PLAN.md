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

### M3 — Ausbau
- [ ] Level-Editor bzw. **Tiled**-Import (TMX)
- [ ] Mehrere Welten/Themes (Eis, Höhle) inkl. eigener FLUX-Kulissen
- [ ] Speichern/Fortschritt, Highscores
- [ ] Gamepad-Unterstützung
- [ ] Boss am Weltende

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
