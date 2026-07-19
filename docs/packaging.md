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

## Flatpak
```bash
flatpak-builder --user --install --force-clean build-dir \
  packaging/flatpak/org.supertux3.SuperTux3.yaml
flatpak run org.supertux3.SuperTux3
```
Der pip-Schritt braucht beim Bauen Netz (pygame-ce-Wheel). Für einen
offline-reproduzierbaren Build die Wheels mit `flatpak-pip-generator` vendorn.

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
