# SuperTux3 installieren & paketieren

Alle Assets sind bereits erzeugt und im Repo enthalten – zum **Spielen** wird nur
Python 3.10+ und **pygame** (empfohlen `pygame-ce`) benötigt.

## Am einfachsten: Nutzer-Installer (ohne Root) — ideal für die Kinderrechner
```bash
bash packaging/install-user.sh
```
Legt ein eigenes venv mit pygame an, kopiert das Spiel nach
`~/.local/share/supertux3-app`, erstellt den Menüeintrag **„SuperTux3"** mit Icon
und den Launcher `~/.local/bin/supertux3`. Funktioniert auf jeder Linux-Distro
(Fedora, Ubuntu, Raspberry Pi OS …) ohne Administratorrechte.

## Systemweit (RPM/DEB via Makefile)
```bash
sudo make install            # nach /usr
sudo make uninstall
```
`make install` kopiert den Spielbaum nach `/usr/share/supertux3`, legt den
Launcher `/usr/bin/supertux3`, den Desktop-Eintrag, AppStream-Metadaten und Icons
an. `PREFIX=` und `DESTDIR=` werden respektiert (für Paketbau).

## RPM (Fedora/Nobara)
```bash
# Tarball nach ~/rpmbuild/SOURCES/supertux3-0.5.0.tar.gz legen, dann:
rpmbuild -ba packaging/rpm/supertux3.spec
```
Abhängigkeit: `python3-pygame` (>= 2). Alternativ `pip install pygame-ce`.

## DEB (Debian/Ubuntu/Raspberry Pi OS)
```bash
cp -r packaging/debian debian
dpkg-buildpackage -us -uc -b
```

## Flatpak (empfohlen zum Weitergeben – 1 Datei, keine Symlinks)

Ein Flatpak-**Bundle** ist eine einzelne `.flatpak`-Datei, die man auf einen
USB-Stick kopieren und auf jedem Linux-Rechner mit Flatpak installieren kann –
ohne Symlink-Probleme (venv/Worktrees etc. sind nicht enthalten).

### Bauen
```bash
# einmalig: Builder (als Flatpak, kein Root) + Runtime/SDK
flatpak install --user -y flathub org.flatpak.Builder \
  org.freedesktop.Platform//25.08 org.freedesktop.Sdk//25.08

# bauen (der pip-Schritt lädt pygame-ce -> Netz nötig) und Bundle exportieren
flatpak run org.flatpak.Builder --user --force-clean --disable-rofiles-fuse \
  --repo=repo build-dir packaging/flatpak/org.supertux3.SuperTux3.yaml
mkdir -p dist
flatpak build-bundle repo dist/supertux3-v1.0.flatpak org.supertux3.SuperTux3
```
Ergebnis: `dist/supertux3-v1.0.flatpak` (~31 MB). Auch als Download am
GitHub-Release v1.0.

### Installieren & Spielen (auf USB-Stick kopieren, dann am Zielrechner)
```bash
flatpak install --user supertux3-v1.0.flatpak    # kein Root nötig
flatpak run org.supertux3.SuperTux3              # oder Menüeintrag "SuperTux3"
```
Voraussetzung am Zielrechner: Flatpak + die Freedesktop-Runtime 25.08 (wird bei
`flatpak install` bei Bedarf automatisch aus Flathub nachgeladen).

### Ziel-Rechner OHNE Internet (Runtime fehlt)
Ist der Zielrechner **offline** und hat die Runtime noch nicht, schlägt die
App-Installation fehl („runtime … not installed"). Dann zusätzlich die
**Runtime-Bundles** mitkopieren (auch am GitHub-Release v1.0):

- `org.freedesktop.Platform-25.08.flatpak`  (Pflicht, ~168 MB)
- `org.freedesktop.Platform.GL.default-25.08.flatpak`  (empfohlen für flüssige Grafik, ~93 MB)

Alle drei `.flatpak`-Dateien auf den USB-Stick, dann am Zielrechner **in dieser
Reihenfolge** (Runtime zuerst, App zuletzt):
```bash
flatpak install --user ./org.freedesktop.Platform-25.08.flatpak
flatpak install --user ./org.freedesktop.Platform.GL.default-25.08.flatpak   # optional
flatpak install --user ./supertux3-v1.0.flatpak
flatpak run org.supertux3.SuperTux3
```
Damit ist **kein Internet** nötig. (Eine evtl. Meldung zur fehlenden
`.Locale`-Erweiterung kann ignoriert werden – das Spiel braucht sie nicht.)

> Offline-reproduzierbar: Für einen Build ganz ohne Netz die pygame-ce-Wheels
> mit `flatpak-pip-generator` vendorn.

## pip (Entwicklung)
```bash
pip install -e .            # editierbar aus dem Repo (findet assets/levels)
supertux3
```
> Hinweis: Ein *nicht*-editierbares `pip install` legt nur das Python-Paket ab;
> die Datendateien werden über `SUPERTUX3_DATA` oder `<prefix>/share/supertux3`
> gefunden (siehe `settings._find_root`). Für Endnutzer sind Nutzer-Installer,
> Distro-Paket oder Flatpak der einfachere Weg.

## Speicherorte
- Spielstand/Optionen: `~/.local/share/supertux3/save.json`
- Selbst gebaute Level (Editor): `~/.local/share/supertux3/levels/`
  (funktioniert auch bei schreibgeschützten Systeminstallationen)

## CLI-Optionen
```
supertux3 --quality fast --fps 30      # schwache Hardware
supertux3 --fullscreen                  # Vollbild erzwingen
supertux3 --level level3.json           # direkt ein Level starten
```
