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

### M2 — Mehr Spiel (nächste Schritte)
- [ ] 2–3 weitere Level + Level-Auswahl / Welt-Karte
- [ ] Power-Up-Zustände (klein/groß, Treffer verkleinert statt sofort Leben weg)
- [ ] 2. Gegnertyp (z.B. fliegend oder springend)
- [ ] Bewegliche Plattformen, Sprungfedern, Checkpoints
- [ ] Partikel & „Juice" (Münz-Funken, Stampf-Staub, Screen-Shake)
- [ ] Pause-Menü, Optionen (Lautstärke, Fenster)

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
- Interne Auflösung 480×270, `pygame.SCALED` fürs Hochskalieren.
- Konstanten zentral in `settings.py`.
- Fehlertolerant: fehlende Assets/kein Audiogerät dürfen nicht crashen.
