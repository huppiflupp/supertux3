#!/usr/bin/env python3
"""8-bit-Chiptune-Generator für SuperTux3 (eigenständige Kompositionen).

Synth-Merkmale wie bei NES-Musik: Pulswellen mit variabler Puls­breite,
Vibrato, Arpeggien (schnell wechselnde Akkordtöne), Dreieck-Bass und
Rausch-Schlagzeug (Kick/Snare/HiHat), alles mit ADSR-Hüllkurve.

Musik → OGG (via ffmpeg), SFX → WAV.
  music/: title, level1(grass), level2(sunset), level3(night), ice, cave, boss
  sfx/:   jump, coin, stomp, hurt, win, spring, grow, checkpoint, throw, star
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

_NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
         "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def freq(name: str) -> float:
    if name == "r":
        return 0.0
    midi = 12 * (int(name[-1]) + 1) + _NOTE[name[:-1]]
    return 440.0 * 2 ** ((midi - 69) / 12)


# --- Oszillator mit Vibrato ---------------------------------------------
def osc(f, n, wave_type="pulse", duty=0.5, vib_depth=0.0, vib_rate=6.0):
    if f <= 0:
        return np.zeros(n)
    t = np.arange(n) / SR
    inst = f * (1.0 + (vib_depth / 100.0) * np.sin(2 * np.pi * vib_rate * t)) \
        if vib_depth else f
    ph = np.cumsum(np.full(n, 2 * np.pi * f / SR)) if not vib_depth \
        else np.cumsum(2 * np.pi * inst / SR)
    p = (ph / (2 * np.pi)) % 1.0
    if wave_type in ("pulse", "square"):
        return np.where(p < duty, 1.0, -1.0)
    if wave_type == "triangle":
        return 2.0 * np.abs(2.0 * p - 1.0) - 1.0
    if wave_type == "saw":
        return 2.0 * p - 1.0
    if wave_type == "sine":
        return np.sin(ph)
    if wave_type == "noise":
        return np.random.uniform(-1, 1, n)
    return np.sin(ph)


def adsr(n, a=0.004, d=0.05, s=0.65, r=0.06):
    env = np.ones(n)
    ai, di, ri = int(a * SR), int(d * SR), int(r * SR)
    ai = min(ai, n)
    if ai:
        env[:ai] = np.linspace(0, 1, ai)
    if di and ai + di < n:
        env[ai:ai + di] = np.linspace(1, s, di)
        env[ai + di:] = s
    if ri and ri < n:
        env[-ri:] *= np.linspace(env[-ri], 0, ri)
    return env


def _spb(bpm):
    return 60.0 / bpm


def lead(notes, bpm, duty=0.5, vol=0.22, vib=0.0, total=None):
    """Monophone Melodie. notes: (name, beats)."""
    total_beats = total if total is not None else sum(b for _, b in notes)
    buf = np.zeros(int(total_beats * _spb(bpm) * SR) + SR)
    pos = 0
    for name, beats in notes:
        n = int(beats * _spb(bpm) * SR)
        if name != "r":
            buf[pos:pos + n] += osc(freq(name), n, "pulse", duty,
                                    vib_depth=vib) * adsr(n) * vol
        pos += n
    return buf


def arp(chords, bpm, vol=0.16, rate=0.0625, duty=0.5):
    """Arpeggien: chords = (["C4","E4","G4"], beats). rate = Note-Länge in Beats."""
    total_beats = sum(b for _, b in chords)
    buf = np.zeros(int(total_beats * _spb(bpm) * SR) + SR)
    pos = 0
    step = int(rate * _spb(bpm) * SR)
    for notes, beats in chords:
        length = int(beats * _spb(bpm) * SR)
        i = 0
        k = 0
        while i < length:
            seg = min(step, length - i)
            nm = notes[k % len(notes)]
            buf[pos + i:pos + i + seg] += osc(freq(nm), seg, "pulse", duty) \
                * adsr(seg, a=0.001, d=0.02, s=0.5, r=0.01) * vol
            i += seg
            k += 1
        pos += length
    return buf


def bass(notes, bpm, vol=0.30):
    total_beats = sum(b for _, b in notes)
    buf = np.zeros(int(total_beats * _spb(bpm) * SR) + SR)
    pos = 0
    for name, beats in notes:
        n = int(beats * _spb(bpm) * SR)
        if name != "r":
            buf[pos:pos + n] += osc(freq(name), n, "triangle") \
                * adsr(n, a=0.002, d=0.04, s=0.8, r=0.04) * vol
        pos += n
    return buf


def drums(pattern, bpm, vol=1.0):
    """pattern: String aus k/s/h/. je 1/8-Beat (0.5 Beats)."""
    step = int(0.5 * _spb(bpm) * SR)
    buf = np.zeros(step * len(pattern) + SR)
    for i, ch in enumerate(pattern):
        pos = i * step
        if ch == "k":
            n = int(0.14 * SR)
            t = np.arange(n) / SR
            f = np.linspace(150, 45, n)
            seg = np.sin(np.cumsum(2 * np.pi * f / SR)) * np.exp(-t * 24) * 0.55
        elif ch == "s":
            n = int(0.14 * SR)
            t = np.arange(n) / SR
            seg = np.random.uniform(-1, 1, n) * np.exp(-t * 26) * 0.35
        elif ch == "h":
            n = int(0.05 * SR)
            t = np.arange(n) / SR
            seg = np.random.uniform(-1, 1, n) * np.exp(-t * 60) * 0.18
        else:
            continue
        buf[pos:pos + len(seg)] += seg * vol
    return buf


def mix(*tracks):
    m = max(len(t) for t in tracks)
    out = np.zeros(m)
    for t in tracks:
        out[:len(t)] += t
    return np.tanh(out * 1.05)


def to_int16(buf):
    return (np.clip(buf, -1, 1) * 32767).astype(np.int16)


def write_wav(path, buf):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(to_int16(buf).tobytes())


def write_ogg(path, buf):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp.wav")
    write_wav(tmp, buf)
    ff = shutil.which("ffmpeg")
    if ff:
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(tmp),
                        "-c:a", "libvorbis", "-qscale:a", "5", str(path)], check=True)
        tmp.unlink(missing_ok=True)
    else:
        tmp.rename(path.with_suffix(".wav"))
    print(f"  music/{path.name}")


def rep(seq, k):
    out = []
    for _ in range(k):
        out += list(seq)
    return out


# =========================================================================
#  Kompositionen (alle eigenständig)
# =========================================================================
def title_music():
    bpm = 120
    mel = [("G4", 1), ("C5", 1), ("E5", 1), ("G5", 1),
           ("F5", 1.5), ("E5", .5), ("D5", 2),
           ("A4", 1), ("D5", 1), ("F5", 1), ("A5", 1),
           ("G5", 1.5), ("F5", .5), ("E5", 2)]
    L = lead(mel, bpm, duty=0.5, vol=0.22, vib=4)
    L = np.concatenate([L, L])
    ch = rep([(["C4", "E4", "G4"], 2), (["F3", "A3", "C4"], 2),
              (["D4", "F4", "A4"], 2), (["G3", "B3", "D4"], 2)], 2)
    A = arp(ch, bpm, vol=0.13)
    B = bass(rep([("C3", 1), ("C3", 1), ("F2", 1), ("F2", 1),
                  ("D3", 1), ("D3", 1), ("G2", 1), ("G2", 1)], 2), bpm, vol=0.26)
    return mix(L, A, B)


def grass_music():
    bpm = 148
    A = [("C5", .5), ("E5", .5), ("G5", .5), ("E5", .5),
         ("F5", .5), ("A5", .5), ("G5", .5), ("E5", .5),
         ("D5", .5), ("F5", .5), ("A5", .5), ("F5", .5),
         ("G5", .5), ("E5", .5), ("C5", 1.0)]
    B = [("E5", .5), ("G5", .5), ("C6", .5), ("G5", .5),
         ("A5", .5), ("F5", .5), ("G5", .5), ("E5", .5),
         ("F5", .5), ("D5", .5), ("E5", .5), ("C5", .5),
         ("G5", .5), ("B4", .5), ("C5", 1.0)]
    L = lead(A + B + A + B, bpm, duty=0.5, vol=0.2, vib=5)
    ch = rep([(["C4", "E4", "G4"], 1), (["F4", "A4", "C5"], 1),
              (["D4", "F4", "A4"], 1), (["G4", "B4", "D5"], 1)], 8)
    A2 = arp(ch, bpm, vol=0.12, rate=0.125)
    bs = bass(rep([("C3", .5), ("C3", .5), ("F2", .5), ("F2", .5),
                   ("D3", .5), ("D3", .5), ("G2", .5), ("G2", .5)], 8), bpm)
    dr = drums(rep("k.h.s.h.", 16), bpm, vol=0.9)
    return mix(L, A2, bs, dr)


def sunset_music():
    bpm = 132
    A = [("A4", .5), ("C5", .5), ("E5", .5), ("A5", .5), ("G5", 1), ("E5", 1),
         ("F5", .5), ("A5", .5), ("G5", .5), ("E5", .5), ("D5", 1), ("C5", 1)]
    L = lead(rep(A, 2), bpm, duty=0.25, vol=0.2, vib=6)
    ch = rep([(["A3", "C4", "E4"], 2), (["F3", "A3", "C4"], 2),
              (["G3", "B3", "D4"], 2), (["E3", "G3", "B3"], 2)], 3)
    A2 = arp(ch, bpm, vol=0.12)
    bs = bass(rep([("A2", 1), ("A2", 1), ("F2", 1), ("F2", 1),
                   ("G2", 1), ("G2", 1), ("E2", 1), ("E2", 1)], 3), bpm)
    dr = drums(rep("k.h.s.h.", 24), bpm, vol=0.8)
    return mix(L, A2, bs, dr)


def night_music():
    bpm = 112
    A = [("E5", 1), ("B4", 1), ("C5", 1), ("G4", 1),
         ("A4", 1), ("E4", 1), ("F4", .5), ("G4", .5), ("A4", 1)]
    L = lead(rep(A, 2), bpm, duty=0.5, vol=0.2, vib=7)
    ch = rep([(["A3", "C4", "E4"], 2), (["E3", "G3", "B3"], 2),
              (["F3", "A3", "C4"], 2), (["C4", "E4", "G4"], 2)], 3)
    A2 = arp(ch, bpm, vol=0.1, rate=0.125)
    bs = bass(rep([("A2", 2), ("E2", 2), ("F2", 2), ("C2", 2)], 3), bpm, vol=0.28)
    dr = drums(rep("k...s...", 24), bpm, vol=0.7)
    return mix(L, A2, bs, dr)


def ice_music():
    bpm = 118
    A = [("E5", 1), ("G5", 1), ("B5", 1), ("A5", 1), ("G5", 1.5), ("E5", .5), ("D5", 2),
         ("C5", 1), ("E5", 1), ("G5", 1), ("F5", 1), ("E5", 1.5), ("D5", .5), ("C5", 2)]
    L = lead(rep(A, 2), bpm, duty=0.5, vol=0.22, vib=8)
    bell = arp(rep([(["C6", "E6", "G6"], 2), (["A5", "C6", "E6"], 2)], 4),
               bpm, vol=0.09, rate=0.25)
    bs = bass(rep([("C3", 2), ("A2", 2), ("F2", 2), ("G2", 2)], 4), bpm, vol=0.24)
    dr = drums(rep("k...h...", 32), bpm, vol=0.6)
    return mix(L, bell, bs, dr)


def cave_music():
    bpm = 128
    A = [("D5", .5), ("F5", .5), ("A5", .5), ("F5", .5), ("E5", 1), ("C5", 1),
         ("D5", .5), ("A4", .5), ("D5", .5), ("F5", .5), ("E5", 1), ("A4", 1)]
    L = lead(rep(A, 2), bpm, duty=0.125, vol=0.2, vib=6)
    ch = rep([(["D4", "F4", "A4"], 1), (["A3", "C4", "E4"], 1),
              (["B3", "D4", "F4"], 1), (["G3", "B3", "D4"], 1)], 6)
    A2 = arp(ch, bpm, vol=0.11, rate=0.0625)
    bs = bass(rep([("D3", .5), ("D2", .5), ("A2", .5), ("A2", .5),
                   ("B2", .5), ("B2", .5), ("G2", .5), ("G2", .5)], 6), bpm)
    dr = drums(rep("k.h.k.s.", 24), bpm, vol=0.9)
    return mix(L, A2, bs, dr)


def egypt_music():
    # Phrygisch-dominant (A B♭ C# D E F G) -> orientalischer Klang
    bpm = 132
    A = [("A4", .5), ("A#4", .5), ("C#5", .5), ("A#4", .5),
         ("A4", .5), ("G4", .5), ("A4", 1.0),
         ("D5", .5), ("C#5", .5), ("A#4", .5), ("A4", .5),
         ("G4", .5), ("F4", .5), ("A4", 1.0)]
    B = [("E5", .5), ("F5", .5), ("E5", .5), ("C#5", .5),
         ("D5", .5), ("A#4", .5), ("A4", 1.0),
         ("C#5", .5), ("D5", .5), ("E5", .5), ("F5", .5),
         ("E5", .5), ("C#5", .5), ("A4", 1.0)]
    L = lead(A + B + A + B, bpm, duty=0.25, vol=0.2, vib=8)
    drone = bass(rep([("A2", 1)], 28), bpm, vol=0.26)
    A2 = arp(rep([(["A3", "C#4", "E4"], 1), (["A3", "D4", "F4"], 1),
                  (["A3", "C#4", "E4"], 1), (["G3", "A#3", "D4"], 1)], 7), bpm, vol=0.11, rate=0.125)
    dr = drums(rep("k.h.k.kh", 14), bpm, vol=0.85)
    return mix(L, drone, A2, dr)


def space_music():
    # schwebend, träumerisch (a-moll mit weiten Arpeggien + Sinus-Lead)
    bpm = 96
    mel = [("A4", 1), ("E5", 1), ("C5", 1), ("D5", 1),
           ("E5", 1.5), ("C5", .5), ("A4", 2),
           ("F4", 1), ("C5", 1), ("A4", 1), ("G4", 1),
           ("E4", 1.5), ("G4", .5), ("A4", 2)]
    L = lead(mel, bpm, duty=0.5, vol=0.18, vib=10)
    L = np.concatenate([L, L])
    twinkle = arp(rep([(["A4", "C5", "E5", "C5"], 2), (["F4", "A4", "C5", "A4"], 2),
                       (["G4", "B4", "D5", "B4"], 2), (["E4", "G4", "C5", "G4"], 2)], 4),
                  bpm, vol=0.10, rate=0.25)
    bs = bass(rep([("A2", 2), ("F2", 2), ("G2", 2), ("E2", 2)], 4), bpm, vol=0.24)
    bs = np.concatenate([bs, bs]) if len(bs) < len(L) else bs
    return mix(L, twinkle, bs)


def boss_music():
    bpm = 160
    # düster, treibend (a-moll/vermindert)
    A = [("A4", .5), ("A4", .5), ("C5", .5), ("A4", .5),
         ("E5", .5), ("D5", .5), ("C5", .5), ("B4", .5),
         ("A4", .5), ("A4", .5), ("C5", .5), ("E5", .5),
         ("F5", .5), ("E5", .5), ("D5", 1.0)]
    L = lead(rep(A, 2), bpm, duty=0.25, vol=0.22, vib=9)
    ch = rep([(["A3", "C4", "E4"], .5), (["A3", "C4", "E4"], .5),
              (["F3", "A3", "C4"], .5), (["F3", "A3", "C4"], .5),
              (["G3", "B3", "D4"], .5), (["G3", "B3", "D4"], .5),
              (["E3", "G#3", "B3"], .5), (["E3", "G#3", "B3"], .5)], 4)
    A2 = arp(ch, bpm, vol=0.13, rate=0.0625, duty=0.25)
    bs = bass(rep([("A2", .25)] * 4 + [("F2", .25)] * 4 +
                  [("G2", .25)] * 4 + [("E2", .25)] * 4, 4), bpm, vol=0.32)
    dr = drums(rep("k.khs.kh", 16), bpm, vol=1.0)
    return mix(L, A2, bs, dr)


# --- SFX -----------------------------------------------------------------
def sfx_jump():
    n = int(0.18 * SR); t = np.arange(n) / SR
    f = np.linspace(320, 720, n)
    return np.sign(np.sin(np.cumsum(2 * np.pi * f / SR))) * np.exp(-t * 9) * 0.4


def sfx_coin():
    a = osc(freq("E6"), int(0.05 * SR), "pulse") * adsr(int(0.05 * SR))
    b = osc(freq("B6"), int(0.14 * SR), "pulse") * adsr(int(0.14 * SR), r=0.1)
    return np.concatenate([a, b]) * 0.32


def sfx_stomp():
    n = int(0.16 * SR); t = np.arange(n) / SR
    noise = np.random.uniform(-1, 1, n) * np.exp(-t * 22)
    tone = np.sin(2 * np.pi * np.linspace(180, 60, n) * t) * np.exp(-t * 12)
    return (noise * 0.4 + tone * 0.6) * 0.5


def sfx_hurt():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = np.linspace(500, 120, n)
    return np.sign(np.sin(np.cumsum(2 * np.pi * f / SR))) * np.exp(-t * 5) * 0.4


def sfx_win():
    return lead([("C5", .12), ("E5", .12), ("G5", .12), ("C6", .3)], 140, vol=0.4)


def sfx_spring():
    n = int(0.22 * SR); t = np.arange(n) / SR
    f = 260 + 520 * np.clip(t * 6, 0, 1) + 40 * np.sin(2 * np.pi * 18 * t)
    return np.sign(np.sin(np.cumsum(2 * np.pi * f / SR))) * np.exp(-t * 5) * 0.4


def sfx_grow():
    return lead([("C5", .08), ("E5", .08), ("G5", .08), ("C6", .1), ("E6", .18)],
                168, duty=0.5, vol=0.38)


def sfx_checkpoint():
    a = osc(freq("G5"), int(0.12 * SR), "sine") * adsr(int(0.12 * SR), r=0.1)
    b = osc(freq("C6"), int(0.30 * SR), "sine") * adsr(int(0.30 * SR), r=0.2)
    return np.concatenate([a, b]) * 0.45


def sfx_throw():
    n = int(0.20 * SR); t = np.arange(n) / SR
    f = np.linspace(900, 300, n)
    noise = np.random.uniform(-1, 1, n) * 0.3
    return (np.sin(np.cumsum(2 * np.pi * f / SR)) * 0.7 + noise) * np.exp(-t * 8) * 0.35


def sfx_star():
    return lead([("G5", .08), ("B5", .08), ("D6", .08), ("G6", .22)],
                180, duty=0.5, vol=0.4, vib=6)


def main():
    np.random.seed(7)
    print("Erzeuge Audio ->", AUD)
    tracks = {
        "title": title_music, "level1": grass_music, "level2": sunset_music,
        "level3": night_music, "ice": ice_music, "cave": cave_music,
        "egypt": egypt_music, "space": space_music, "boss": boss_music,
    }
    for name, fn in tracks.items():
        write_ogg(AUD / "music" / f"{name}.ogg", fn())
    sfx = {"jump": sfx_jump, "coin": sfx_coin, "stomp": sfx_stomp, "hurt": sfx_hurt,
           "win": sfx_win, "spring": sfx_spring, "grow": sfx_grow,
           "checkpoint": sfx_checkpoint, "throw": sfx_throw, "star": sfx_star}
    for name, fn in sfx.items():
        write_wav(AUD / "sfx" / f"{name}.wav", fn())
        print(f"  sfx/{name}.wav")
    print("Fertig.")


if __name__ == "__main__":
    main()
