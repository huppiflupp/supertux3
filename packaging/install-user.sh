#!/usr/bin/env bash
# Installiert SuperTux3 OHNE Root ins Benutzerverzeichnis (~/.local).
# Ideal für die Kinderrechner: legt ein eigenes venv mit pygame an und trägt
# einen Menüeintrag ("SuperTux3") samt Icon ein.
set -e
cd "$(dirname "$0")/.."          # Projektwurzel
SRC="$(pwd)"

DATA="${XDG_DATA_HOME:-$HOME/.local/share}/supertux3-app"
BIN="$HOME/.local/bin"
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICONS="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor"

echo "[SuperTux3] Installiere nach $DATA ..."
mkdir -p "$DATA" "$BIN" "$APPS" \
         "$ICONS/256x256/apps" "$ICONS/128x128/apps" "$ICONS/64x64/apps"

# Spieldateien kopieren
cp -r "$SRC/src" "$SRC/assets" "$SRC/levels" "$DATA/"

# venv mit pygame anlegen
echo "[SuperTux3] Erstelle venv + installiere pygame-ce ..."
python3 -m venv "$DATA/venv"
"$DATA/venv/bin/pip" install -q --upgrade pip
"$DATA/venv/bin/pip" install -q pygame-ce

# Launcher
cat > "$BIN/supertux3" <<EOF
#!/bin/sh
export SUPERTUX3_DATA="$DATA"
exec env PYTHONPATH="$DATA/src" "$DATA/venv/bin/python" -m supertux3 "\$@"
EOF
chmod +x "$BIN/supertux3"

# Menüeintrag + Icons
sed "s|Exec=supertux3|Exec=$BIN/supertux3|" \
    "$SRC/packaging/org.supertux3.SuperTux3.desktop" > "$APPS/org.supertux3.SuperTux3.desktop"
cp "$SRC/assets/icon/supertux3-256.png" "$ICONS/256x256/apps/org.supertux3.SuperTux3.png"
cp "$SRC/assets/icon/supertux3-128.png" "$ICONS/128x128/apps/org.supertux3.SuperTux3.png"
cp "$SRC/assets/icon/supertux3-64.png"  "$ICONS/64x64/apps/org.supertux3.SuperTux3.png"

echo
echo "[SuperTux3] Fertig! Starten mit:  $BIN/supertux3"
echo "  (Ist ~/.local/bin im PATH, genügt 'supertux3'. Sonst der Menüeintrag 'SuperTux3'.)"
