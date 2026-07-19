Name:           supertux3
Version:        0.5.0
Release:        1%{?dist}
Summary:        Ein 2D-Jump'n'Run mit dem Pinguin Pengu

License:        GPL-3.0-or-later
URL:            https://github.com/huppiflupp/supertux3
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python3 >= 3.10
# Klassisches python3-pygame (>=2) funktioniert; alternativ pygame-ce via pip.
Requires:       python3-pygame >= 2

%description
SuperTux3 ist ein 2D-Jump'n'Run im Geiste von SuperTux: 15 Level über fünf
Welten, Münzen und Sterne, stampfbare Gegner, zwei Bosse, In-Game-Level-Editor,
Gamepad-Unterstützung und ein Schnell-Grafikmodus für schwache Hardware.

%prep
%autosetup

%build
# Nichts zu kompilieren (reines Python).

%install
make install PREFIX=%{_prefix} DESTDIR=%{buildroot}

%files
%{_bindir}/supertux3
%{_datadir}/supertux3/
%{_datadir}/applications/org.supertux3.SuperTux3.desktop
%{_datadir}/metainfo/org.supertux3.SuperTux3.metainfo.xml
%{_datadir}/icons/hicolor/*/apps/org.supertux3.SuperTux3.png

%changelog
* Sun Jul 19 2026 huppiflupp - 0.5.0-1
- Erste Paketierung (M5): 15 Level, Editor, Optionen, Pi-Modus.
