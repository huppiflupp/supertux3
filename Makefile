# Installation von SuperTux3 (für RPM/DEB/Flatpak/`sudo make install`).
# Der komplette Spielbaum landet in $(DATADIR); ein Launcher kommt nach $(BINDIR).
PREFIX  ?= /usr
DESTDIR ?=
BINDIR   = $(PREFIX)/bin
DATADIR  = $(PREFIX)/share/supertux3
APPDIR   = $(PREFIX)/share/applications
ICONDIR  = $(PREFIX)/share/icons/hicolor
METADIR  = $(PREFIX)/share/metainfo

.PHONY: install uninstall assets

# Assets/Level (neu) erzeugen – nur nötig, wenn sie fehlen (venv mit numpy/Pillow)
assets:
	python3 tools/asset_pipeline/gen_pixelart.py
	python3 tools/asset_pipeline/gen_audio.py
	python3 tools/asset_pipeline/gen_icon.py
	python3 tools/build_levels.py

install:
	install -d $(DESTDIR)$(DATADIR)/src
	cp -r src/supertux3 $(DESTDIR)$(DATADIR)/src/
	cp -r assets levels $(DESTDIR)$(DATADIR)/
	install -d $(DESTDIR)$(BINDIR)
	sed 's|@DATADIR@|$(DATADIR)|g' packaging/supertux3.in > $(DESTDIR)$(BINDIR)/supertux3
	chmod 755 $(DESTDIR)$(BINDIR)/supertux3
	install -Dm644 packaging/org.supertux3.SuperTux3.desktop \
		$(DESTDIR)$(APPDIR)/org.supertux3.SuperTux3.desktop
	install -Dm644 packaging/org.supertux3.SuperTux3.metainfo.xml \
		$(DESTDIR)$(METADIR)/org.supertux3.SuperTux3.metainfo.xml
	install -Dm644 assets/icon/supertux3-256.png \
		$(DESTDIR)$(ICONDIR)/256x256/apps/org.supertux3.SuperTux3.png
	install -Dm644 assets/icon/supertux3-128.png \
		$(DESTDIR)$(ICONDIR)/128x128/apps/org.supertux3.SuperTux3.png
	install -Dm644 assets/icon/supertux3-64.png \
		$(DESTDIR)$(ICONDIR)/64x64/apps/org.supertux3.SuperTux3.png

uninstall:
	rm -rf $(DESTDIR)$(DATADIR)
	rm -f  $(DESTDIR)$(BINDIR)/supertux3
	rm -f  $(DESTDIR)$(APPDIR)/org.supertux3.SuperTux3.desktop
	rm -f  $(DESTDIR)$(METADIR)/org.supertux3.SuperTux3.metainfo.xml
	rm -f  $(DESTDIR)$(ICONDIR)/*/apps/org.supertux3.SuperTux3.png
