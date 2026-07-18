#!/usr/bin/env python3
"""Prozeduraler Chiptune-Generator für SuperTux3.

Synthetisiert eine fröhliche Level-Musik und ein Titelthema (loopbar) sowie die
Soundeffekte – komplett offline mit numpy. Musik wird als OGG (via ffmpeg,
klein & loopbar) exportiert, SFX als WAV.

Ausgabe:
  assets/audio/music/{title,level1}.ogg
  assets/audio/sfx/{jump,coin,stomp,hurt,win}.wav
"""
from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "assets" / "audio"
SR = 44100

# --- Notennamen -> Frequenz ---------------------------------------------
_NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
         "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def freq(name: str) -> float:
    if name == "r":
        return 0.0
    pitch = name[:-1]
    octave = int(name[-1])
    midi = 12 * (octave + 1) + _NOTE[pitch]
    return 440.0 * 2 ** ((midi - 69) / 12)


# --- Oszillatoren --------------------------------------------------------
def osc(f: float, n: int, wave_type: str = "square", duty: float = 0.5) -> np.ndarray:
    if f <= 0:
        return np.zeros(n)
    t = np.arange(n) / SR
    ph = (t * f) % 1.0
    if wave_type == "square":
        return np.where(ph < duty, 1.0, -1.0)
    if wave_type == "triangle":
        return 2.0 * np.abs(2.0 * ph - 1.0) - 1.0
    if wave_type == "saw":
        return 2.0 * ph - 1.0
    if wave_type == "sine":
        return np.sin(2 * np.pi * ph)
    if wave_type == "noise":
        return np.random.uniform(-1, 1, n)
    return np.sin(2 * np.pi * ph)


def envelope(n: int, a=0.005, d=0.03, s=0.7, r=0.04) -> np.ndarray:
    env = np.ones(n)
    ai, di, ri = int(a * SR), int(d * SR), int(r * SR)
    ai = min(ai, n)
    if ai:
        env[:ai] = np.linspace(0, 1, ai)
    if di and ai + di < n:
        env[ai:ai + di] = np.linspace(1, s, di)
        env[ai + di:] = s
    if ri and ri < n:
        env[-ri:] *= np.linspace(1, 0, ri)
    return env


def render_track(notes, bpm, wave_type="square", duty=0.5, vol=0.25,
                 total_beats=None) -> np.ndarray:
    """notes: Liste (name, beats). Gibt einen mono float-Buffer zurück."""
    spb = 60.0 / bpm
    if total_beats is None:
        total_beats = sum(b for _, b in notes)
    total = int(total_beats * spb * SR) + SR
    buf = np.zeros(total)
    pos = 0
    for name, beats in notes:
        n = int(beats * spb * SR)
        if name != "r":
            seg = osc(freq(name), n, wave_type, duty) * envelope(n) * vol
            buf[pos:pos + n] += seg
        pos += n
    return buf


def mix(*tracks) -> np.ndarray:
    m = max(len(t) for t in tracks)
    out = np.zeros(m)
    for t in tracks:
        out[:len(t)] += t
    # sanfte Sättigung gegen Clipping
    return np.tanh(out * 1.1)


def to_int16(buf: np.ndarray) -> np.ndarray:
    buf = np.clip(buf, -1, 1)
    return (buf * 32767).astype(np.int16)


def write_wav(path: Path, buf: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = to_int16(buf)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def write_ogg(path: Path, buf: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp.wav")
    write_wav(tmp, buf)
    ff = shutil.which("ffmpeg")
    if ff:
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(tmp),
                        "-c:a", "libvorbis", "-qscale:a", "5", str(path)], check=True)
        tmp.unlink(missing_ok=True)
        print(f"  music/{path.name}")
    else:
        # Fallback: WAV unter .ogg-Namen ist ungültig -> als .wav behalten
        tmp.rename(path.with_suffix(".wav"))
        print(f"  music/{path.stem}.wav (ffmpeg fehlt -> WAV)")


# =========================================================================
#  Kompositionen
# =========================================================================
def level_music() -> np.ndarray:
    bpm = 144
    # Melodie (fröhlich, C-Dur), Achtel
    A = [("C5", .5), ("E5", .5), ("G5", .5), ("E5", .5),
         ("F5", .5), ("A5", .5), ("G5", .5), ("E5", .5),
         ("D5", .5), ("F5", .5), ("A5", .5), ("F5", .5),
         ("G5", .5), ("E5", .5), ("C5", .5), ("r", .5)]
    B = [("E5", .5), ("G5", .5), ("C6", .5), ("G5", .5),
         ("A5", .5), ("F5", .5), ("G5", .5), ("E5", .5),
         ("F5", .5), ("D5", .5), ("E5", .5), ("C5", .5),
         ("D5", .5), ("G4", .5), ("C5", 1.0)]
    melody = A + B + A + B
    lead = render_track(melody, bpm, "square", duty=0.5, vol=0.22)

    # Bass (Viertel, Grundtöne pro Takt)
    roots = ["C3", "F3", "D3", "G3", "C3", "A2", "F3", "G3"]
    bass_notes = []
    for r in roots * 2:
        bass_notes += [(r, .5), (r, .5), (r, .5), (r, .5)]
    bass = render_track(bass_notes, bpm, "triangle", vol=0.30)

    # Perkussion: Hi-Hat auf Achteln, Kick auf Vierteln
    beats = sum(b for _, b in melody)
    hats = render_track([("A6", .25)] * int(beats * 4), bpm, "noise", vol=0.05)
    kick_notes = []
    for _ in range(int(beats)):
        kick_notes += [("C2", .5), ("r", .5)]
    kick = render_track(kick_notes, bpm, "sine", vol=0.35)
    return mix(lead, bass, hats, kick)


def title_music() -> np.ndarray:
    bpm = 120
    melody = [("G4", 1), ("C5", 1), ("E5", 1), ("G5", 1),
              ("F5", 1.5), ("E5", .5), ("D5", 2),
              ("A4", 1), ("D5", 1), ("F5", 1), ("A5", 1),
              ("G5", 1.5), ("F5", .5), ("E5", 2)]
    lead = render_track(melody, bpm, "square", duty=0.5, vol=0.22)
    lead = np.concatenate([lead, lead])
    roots = ["C3", "F3", "D3", "G3"] * 2
    bass_notes = []
    for r in roots:
        bass_notes += [(r, 1), (r, 1)]
    bass = render_track(bass_notes, bpm, "triangle", vol=0.28)
    bass = np.concatenate([bass, bass])
    return mix(lead, bass)


# --- SFX -----------------------------------------------------------------
def sfx_jump() -> np.ndarray:
    n = int(0.18 * SR)
    t = np.arange(n) / SR
    f = np.linspace(320, 720, n)
    ph = np.cumsum(2 * np.pi * f / SR)
    return np.sign(np.sin(ph)) * np.exp(-t * 9) * 0.4


def sfx_coin() -> np.ndarray:
    a = osc(freq("E6"), int(0.05 * SR), "square") * envelope(int(0.05 * SR))
    b = osc(freq("B6"), int(0.14 * SR), "square") * envelope(int(0.14 * SR), r=0.1)
    return np.concatenate([a, b]) * 0.35


def sfx_stomp() -> np.ndarray:
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    noise = np.random.uniform(-1, 1, n) * np.exp(-t * 22)
    tone = np.sin(2 * np.pi * np.linspace(180, 60, n) * t) * np.exp(-t * 12)
    return (noise * 0.4 + tone * 0.6) * 0.5


def sfx_hurt() -> np.ndarray:
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = np.linspace(500, 120, n)
    ph = np.cumsum(2 * np.pi * f / SR)
    return np.sign(np.sin(ph)) * np.exp(-t * 5) * 0.4


def sfx_win() -> np.ndarray:
    seq = [("C5", .12), ("E5", .12), ("G5", .12), ("C6", .3)]
    return render_track(seq, 140, "square", vol=0.4)


def sfx_spring() -> np.ndarray:
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    f = 260 + 520 * np.clip(t * 6, 0, 1) + 40 * np.sin(2 * np.pi * 18 * t)
    ph = np.cumsum(2 * np.pi * f / SR)
    return np.sign(np.sin(ph)) * np.exp(-t * 5) * 0.4


def sfx_grow() -> np.ndarray:
    seq = [("C5", .08), ("E5", .08), ("G5", .08), ("C6", .1), ("E6", .18)]
    return render_track(seq, 168, "square", duty=0.5, vol=0.38)


def sfx_checkpoint() -> np.ndarray:
    a = osc(freq("G5"), int(0.12 * SR), "sine") * envelope(int(0.12 * SR), r=0.1)
    b = osc(freq("C6"), int(0.30 * SR), "sine") * envelope(int(0.30 * SR), r=0.2)
    return np.concatenate([a, b]) * 0.45


def sfx_throw() -> np.ndarray:
    n = int(0.20 * SR)
    t = np.arange(n) / SR
    f = np.linspace(900, 300, n)
    ph = np.cumsum(2 * np.pi * f / SR)
    noise = np.random.uniform(-1, 1, n) * 0.3
    return (np.sin(ph) * 0.7 + noise) * np.exp(-t * 8) * 0.35


# --- weitere Musik -------------------------------------------------------
def level2_music() -> np.ndarray:
    bpm = 156
    A = [("A4", .5), ("C5", .5), ("E5", .5), ("A5", .5),
         ("G5", .5), ("E5", .5), ("C5", .5), ("D5", .5),
         ("F5", .5), ("A5", .5), ("G5", .5), ("E5", .5),
         ("D5", .5), ("B4", .5), ("C5", 1.0)]
    B = [("E5", .5), ("A5", .5), ("G5", .5), ("F5", .5),
         ("E5", .5), ("D5", .5), ("C5", .5), ("B4", .5),
         ("A4", .5), ("C5", .5), ("E5", .5), ("D5", .5),
         ("C5", .5), ("E5", .5), ("A5", 1.0)]
    melody = A + B + A + B
    lead = render_track(melody, bpm, "square", duty=0.35, vol=0.22)
    roots = ["A2", "F2", "C3", "G2", "D3", "B2", "F2", "E3"]
    bass_notes = []
    for r in (roots * 2):
        bass_notes += [(r, .5)] * 4
    bass = render_track(bass_notes, bpm, "triangle", vol=0.30)
    beats = sum(b for _, b in melody)
    kick_notes = []
    for _ in range(int(beats)):
        kick_notes += [("C2", .5), ("r", .5)]
    kick = render_track(kick_notes, bpm, "sine", vol=0.32)
    hats = render_track([("A6", .25)] * int(beats * 4), bpm, "noise", vol=0.05)
    return mix(lead, bass, kick, hats)


def ice_music() -> np.ndarray:
    bpm = 116
    melody = [("E5", 1), ("G5", 1), ("B5", 1), ("A5", 1),
              ("G5", 1.5), ("E5", .5), ("D5", 2),
              ("C5", 1), ("E5", 1), ("G5", 1), ("F5", 1),
              ("E5", 1.5), ("D5", .5), ("C5", 2)]
    lead = render_track(melody, bpm, "triangle", vol=0.26)
    lead = np.concatenate([lead, lead])
    bell = render_track([("C6", .5), ("r", 1.5)] * 8, bpm, "sine", vol=0.14)
    roots = ["C3", "A2", "F2", "G2"] * 2
    bass = render_track([(r, 2) for r in roots], bpm, "triangle", vol=0.24)
    bass = np.concatenate([bass, bass])
    return mix(lead, bell, bass)


def main() -> None:
    np.random.seed(7)
    print("Erzeuge Audio ->", AUD)
    write_ogg(AUD / "music" / "level1.ogg", level_music())
    write_ogg(AUD / "music" / "level2.ogg", level2_music())
    write_ogg(AUD / "music" / "ice.ogg", ice_music())
    write_ogg(AUD / "music" / "title.ogg", title_music())
    for name, fn in [("jump", sfx_jump), ("coin", sfx_coin), ("stomp", sfx_stomp),
                     ("hurt", sfx_hurt), ("win", sfx_win), ("spring", sfx_spring),
                     ("grow", sfx_grow), ("checkpoint", sfx_checkpoint), ("throw", sfx_throw)]:
        write_wav(AUD / "sfx" / f"{name}.wav", fn())
        print(f"  sfx/{name}.wav")
    print("Fertig.")


if __name__ == "__main__":
    main()
