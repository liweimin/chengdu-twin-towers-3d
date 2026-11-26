#!/usr/bin/env python3
"""
Procedural Original Soundtrack & Natural Ambient Soundscape Generator
for "纸船与小溪" (12.5s, 48kHz 16-bit Stereo WAV, zero external dependencies).

Layers:
  1. Babbling brook ambience (multi-band filtered water flow + gentle bubbling droplets)
  2. Story-synced Foley:
     - 1.55s: Paper boat gently touching the stream (soft water plop & tiny splash)
     - 3.5s & 6.3s: Distant warm woodland songbird chirps
     - 7.5s - 11.4s: Soft duckling paddling ripples
     - 8.45s & 9.55s: Two gentle, cute duckling peep/quacks
     - 8.95s: Soft water push swish as duckling nudges the boat
  3. Original Picture-Book Musical Score (F Major, gentle 3/4 waltz, ~108 BPM):
     - Karplus-Strong plucked acoustic harp / nylon guitar arpeggios
     - Delicate celesta / music-box melody
     - Warm sustained felt-cello bass harmony
     - Stereo algorithmic reverb & soft-clip mastering
"""

import math
import os
import random
import struct
import wave

SAMPLE_RATE = 48000
DURATION = 12.5
NUM_SAMPLES = int(SAMPLE_RATE * DURATION)
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "soundtrack.wav")


def midi_to_freq(midi_note: float) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69.0) / 12.0))


def clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return lo if v < lo else (hi if v > hi else v)


def add_stereo(buf_l, buf_r, start_sec: float, mono_samples, gain: float = 1.0, pan: float = 0.0):
    """Mix a mono buffer into stereo buffers with constant-power panning (-1..+1)."""
    start_idx = int(start_sec * SAMPLE_RATE)
    if start_idx >= NUM_SAMPLES:
        return
    angle = (pan + 1.0) * 0.25 * math.pi
    gl = gain * math.cos(angle)
    gr = gain * math.sin(angle)
    end_idx = min(NUM_SAMPLES, start_idx + len(mono_samples))
    i0 = max(0, start_idx)
    for idx in range(i0, end_idx):
        s = mono_samples[idx - start_idx]
        buf_l[idx] += s * gl
        buf_r[idx] += s * gr


# =============================================================================
# 1. INSTRUMENT SYNTHESIZERS (ZERO DEPENDENCIES)
# =============================================================================

def synth_plucked_harp(freq: float, dur: float, brightness: float = 0.52, seed: int = 1):
    """Warm Karplus-Strong plucked harp / nylon guitar string."""
    n = int(dur * SAMPLE_RATE)
    delay = max(2, int(round(SAMPLE_RATE / freq)))
    rng = random.Random(seed)
    # Softly filtered noise burst for warm finger-plucked timbre
    ring = [0.0] * delay
    prev = 0.0
    for i in range(delay):
        raw = rng.uniform(-1.0, 1.0)
        prev = prev * (1.0 - brightness) + raw * brightness
        ring[i] = prev
    # Remove DC offset
    mean = sum(ring) / delay
    ring = [x - mean for x in ring]

    out = [0.0] * n
    decay = 0.9968 if freq < 350 else 0.9955
    pos = 0
    attack_len = int(0.004 * SAMPLE_RATE)
    release_len = int(0.06 * SAMPLE_RATE)
    for i in range(n):
        nxt = (pos + 1) % delay
        val = 0.5 * (ring[pos] + ring[nxt]) * decay
        ring[pos] = val
        pos = nxt
        env = 1.0
        if i < attack_len:
            env = i / attack_len
        elif i > n - release_len:
            env = max(0.0, (n - i) / release_len)
        out[i] = val * env
    return out


def synth_celesta(freq: float, dur: float):
    """Delicate storybook celesta / music-box bell tone."""
    n = int(dur * SAMPLE_RATE)
    out = [0.0] * n
    w = 2.0 * math.pi * freq / SAMPLE_RATE
    # Warm bell harmonics (fundamental + soft 2nd + gentle 3rd + faint 4.02 shimmer)
    for i in range(n):
        t = i / SAMPLE_RATE
        env_a = min(1.0, t / 0.008)
        e1 = math.exp(-t * 2.4)
        e2 = math.exp(-t * 4.5)
        e3 = math.exp(-t * 7.8)
        s = (
            1.00 * math.sin(w * i) * e1
            + 0.34 * math.sin(2.0 * w * i) * e2
            + 0.12 * math.sin(3.0 * w * i) * e3
            + 0.05 * math.sin(4.02 * w * i) * math.exp(-t * 11.0)
        )
        out[i] = s * env_a * 0.55
    return out


def synth_warm_cello(freq: float, dur: float):
    """Soft, bowed warm cello / felt pad bass note."""
    n = int(dur * SAMPLE_RATE)
    out = [0.0] * n
    w = 2.0 * math.pi * freq / SAMPLE_RATE
    atk = min(0.45, dur * 0.25)
    rel = min(0.55, dur * 0.30)
    for i in range(n):
        t = i / SAMPLE_RATE
        vib = 1.0 + 0.003 * math.sin(2.0 * math.pi * 4.6 * t) * min(1.0, t / 0.6)
        ph = w * i * vib
        s = (
            0.72 * math.sin(ph)
            + 0.24 * math.sin(2.0 * ph + 0.2)
            + 0.08 * math.sin(3.0 * ph + 0.5)
        )
        if t < atk:
            env = 0.5 - 0.5 * math.cos(math.pi * t / atk)
        elif t > dur - rel:
            env = 0.5 - 0.5 * math.cos(math.pi * max(0.0, dur - t) / rel)
        else:
            env = 1.0
        out[i] = s * env * 0.42
    return out


# =============================================================================
# 2. AMBIENT STREAM & STORY-SYNCED FOLEY
# =============================================================================

def generate_babbling_brook(buf_l, buf_r):
    """Layered organic babbling brook soundscape across full 12.5s."""
    rng = random.Random(20261126)
    # 3-tap pink/brown filtered stream beds (left & right decorrelated)
    lp1_l = lp2_l = hp_l = 0.0
    lp1_r = lp2_r = hp_r = 0.0

    for i in range(NUM_SAMPLES):
        t = i / SAMPLE_RATE
        # Subtle dynamic curve: calm at launch bank, livelier around stones (3.5-7.5s), open in glade
        stone_boost = math.exp(-((t - 5.2) / 2.2) ** 2) * 0.25
        env_master = min(1.0, t / 0.8) * min(1.0, (DURATION - t) / 0.9) * (0.85 + stone_boost)

        nl = rng.uniform(-1.0, 1.0)
        nr = rng.uniform(-1.0, 1.0)

        # Warm low-mid water body (~350Hz lowpass)
        lp1_l += 0.045 * (nl - lp1_l)
        lp1_r += 0.045 * (nr - lp1_r)

        # Gentle rippling mid-high water shimmer (~1.2kHz bandpass-ish)
        lp2_l += 0.19 * (nl - lp2_l)
        hp_l += 0.06 * (lp2_l - hp_l)
        shimmer_l = lp2_l - hp_l

        lp2_r += 0.19 * (nr - lp2_r)
        hp_r += 0.06 * (lp2_r - hp_r)
        shimmer_r = lp2_r - hp_r

        # Organic LFO water flow swell
        swell_l = 0.78 + 0.22 * math.sin(2.0 * math.pi * 0.37 * t + 0.4)
        swell_r = 0.78 + 0.22 * math.sin(2.0 * math.pi * 0.43 * t + 1.9)

        buf_l[i] += (lp1_l * 0.26 * swell_l + shimmer_l * 0.11 * swell_r) * env_master
        buf_r[i] += (lp1_r * 0.26 * swell_r + shimmer_r * 0.11 * swell_l) * env_master

    # Add dozens of delicate water-bubble "bloop" droplets along the brook
    for k in range(46):
        bt = rng.uniform(0.2, DURATION - 0.4)
        f0 = rng.uniform(420.0, 1080.0)
        bdur = rng.uniform(0.032, 0.068)
        bn = int(bdur * SAMPLE_RATE)
        bubble = [0.0] * bn
        phase = 0.0
        for j in range(bn):
            u = j / bn
            # Classic Minnaert rising-pitch water bubble chirp
            inst_f = f0 * (1.0 + 0.58 * u * u)
            phase += 2.0 * math.pi * inst_f / SAMPLE_RATE
            env = math.sin(math.pi * u) * math.exp(-u * 2.2)
            bubble[j] = math.sin(phase) * env
        add_stereo(buf_l, buf_r, bt, bubble, gain=rng.uniform(0.014, 0.036), pan=rng.uniform(-0.75, 0.75))


def synth_water_plop(dur: float = 0.26):
    """Soft gentle water touch/plop when the child places the paper boat in the stream."""
    rng = random.Random(404)
    n = int(dur * SAMPLE_RATE)
    out = [0.0] * n
    phase = 0.0
    lp = 0.0
    for i in range(n):
        t = i / SAMPLE_RATE
        u = i / n
        # Rising water-drop resonant bubble + brief soft splash hiss
        f = 320.0 * (1.0 + 1.35 * (u ** 1.4))
        phase += 2.0 * math.pi * f / SAMPLE_RATE
        drop = math.sin(phase) * math.exp(-t * 19.0) * min(1.0, t / 0.008)
        lp += 0.22 * (rng.uniform(-1.0, 1.0) - lp)
        splash = lp * math.exp(-t * 14.0) * min(1.0, t / 0.015)
        out[i] = drop * 0.55 + splash * 0.35
    return out


def synth_songbird(notes_hz, dur_each: float = 0.14):
    """Warm, pastoral distant woodland songbird chirp."""
    gap = int(0.04 * SAMPLE_RATE)
    out = []
    for f_start, f_end in notes_hz:
        n = int(dur_each * SAMPLE_RATE)
        phase = 0.0
        for i in range(n):
            u = i / n
            f = f_start + (f_end - f_start) * (u ** 0.7) + math.sin(u * math.pi * 6) * 35.0
            phase += 2.0 * math.pi * f / SAMPLE_RATE
            env = math.sin(math.pi * u) ** 1.3
            out.append(math.sin(phase) * env * 0.24)
        out.extend([0.0] * gap)
    return out


def synth_duckling_peep(base_freq: float = 640.0, dur: float = 0.19):
    """Cute, warm, gentle baby duckling 'peep-quack' (never harsh)."""
    n = int(dur * SAMPLE_RATE)
    out = [0.0] * n
    phase = 0.0
    lp = 0.0
    for i in range(n):
        u = i / n
        # Slight upward-then-downward vocal inflection
        pitch_curve = 1.0 + 0.18 * math.sin(math.pi * (u ** 0.75)) - 0.08 * u
        f = base_freq * pitch_curve
        phase += 2.0 * math.pi * f / SAMPLE_RATE
        # Soft nasal reed-like harmonic blend
        raw = (
            0.55 * math.sin(phase)
            + 0.35 * math.sin(2.0 * phase + 0.3)
            + 0.18 * math.sin(3.0 * phase)
            + 0.07 * math.sin(4.0 * phase)
        )
        # Gentle lowpass smoothing for cozy picture-book warmth
        lp += 0.25 * (raw - lp)
        env = (math.sin(math.pi * u) ** 0.9) * math.exp(-u * 1.1)
        out[i] = lp * env * 0.42
    return out


def synth_paddle_splash(dur: float = 0.16, seed: int = 1):
    rng = random.Random(seed)
    n = int(dur * SAMPLE_RATE)
    out = [0.0] * n
    lp = hp = 0.0
    for i in range(n):
        u = i / n
        x = rng.uniform(-1.0, 1.0)
        lp += 0.24 * (x - lp)
        hp += 0.07 * (lp - hp)
        env = math.sin(math.pi * u) * math.exp(-u * 2.5)
        out[i] = (lp - hp) * env * 0.35
    return out


# =============================================================================
# 3. ORIGINAL MUSICAL COMPOSITION (F MAJOR, TENDER PICTURE-BOOK WALTZ)
# =============================================================================

def compose_music(buf_l, buf_r):
    beat = 60.0 / 108.0  # ~0.5556s per beat (3 beats per measure = 1.667s)

    # Warm chord progression (7 measures covering 0.15s .. 12.2s):
    # M1: Fmaj7  (F3, C4, E4, A4)
    # M2: Dm7    (D3, A3, C4, F4)
    # M3: Bbmaj7 (Bb2, F3, A3, D4)
    # M4: C9sus4 (C3, G3, Bb3, D4, G4)
    # M5: Fmaj7  (F3, C4, E4, A4)   -- stream opens toward sunlight
    # M6: Bbmaj7 (Bb2, F3, A3, D4)  -- duckling arrives & nudges boat!
    # M7: C11 -> Fadd9 (F3, C4, G4, A4, C5, F5) -- radiant sunlit finale!
    chords = [
        (0.15, [53, 60, 64, 69, 72], 41),  # M1: Fmaj7
        (1.82, [50, 57, 60, 65, 69], 38),  # M2: Dm7
        (3.48, [46, 53, 57, 62, 65], 34),  # M3: Bbmaj7
        (5.15, [48, 55, 58, 62, 67], 36),  # M4: C9sus4
        (6.82, [53, 60, 64, 69, 72], 41),  # M5: Fmaj7
        (8.48, [46, 53, 57, 62, 69], 34),  # M6: Bbmaj7
        (10.10, [53, 60, 65, 67, 69, 72, 77], 41),  # M7: Fadd9 sunlit shimmer!
    ]

    # Harp arpeggios & warm cello bass
    note_seed = 100
    for idx, (t0, notes, bass_midi) in enumerate(chords):
        # Warm sustained cello bass
        cello_dur = 2.25 if idx == len(chords) - 1 else 1.75
        cello = synth_warm_cello(midi_to_freq(bass_midi), cello_dur)
        add_stereo(buf_l, buf_r, t0, cello, gain=0.19, pan=-0.12)

        # Flowing acoustic harp arpeggio
        if idx < len(chords) - 1:
            step = beat * 0.5  # eighth notes in gentle 3/4
            pattern = [0, 1, 2, 3, 4, 2]
            for p_i, n_i in enumerate(pattern):
                nt = t0 + p_i * step
                midi = notes[n_i % len(notes)]
                harp = synth_plucked_harp(midi_to_freq(midi), 1.65, brightness=0.48, seed=note_seed)
                note_seed += 1
                pan = -0.28 + (p_i / 5.0) * 0.56
                add_stereo(buf_l, buf_r, nt, harp, gain=0.145, pan=pan)
        else:
            # Radiant golden harp roll at the sunlit finale!
            for p_i, midi in enumerate(notes):
                nt = t0 + p_i * 0.085
                harp = synth_plucked_harp(midi_to_freq(midi), 2.35, brightness=0.56, seed=note_seed)
                note_seed += 1
                pan = -0.35 + (p_i / (len(notes) - 1)) * 0.70
                add_stereo(buf_l, buf_r, nt, harp, gain=0.155, pan=pan)

    # Original Celesta / Music-Box Melody (tender, lyrical, synced to story beats)
    # (time_sec, midi_note, duration, gain)
    melody = [
        # Act I: Child gently lowers paper boat into the stream
        (0.42, 72, 0.90, 0.14),  # C5
        (0.98, 74, 0.75, 0.14),  # D5
        (1.55, 77, 1.35, 0.18),  # F5 (boat touches water!)
        (2.38, 76, 0.70, 0.14),  # E5
        (2.94, 72, 0.85, 0.13),  # C5

        # Act II: Drifting past mossy stones and swirling autumn leaves
        (3.55, 74, 0.95, 0.15),  # D5
        (4.12, 72, 0.65, 0.13),  # C5
        (4.62, 69, 0.85, 0.14),  # A4
        (5.20, 72, 1.15, 0.15),  # C5
        (5.95, 74, 0.75, 0.14),  # D5
        (6.42, 76, 0.85, 0.15),  # E5

        # Act III: Duckling swims in & pushes boat toward the golden sunlight
        (6.95, 77, 1.05, 0.17),  # F5
        (7.65, 79, 0.85, 0.16),  # G5 (duckling enters!)
        (8.22, 81, 0.95, 0.18),  # A5
        (8.88, 79, 0.75, 0.17),  # G5 (beak nudge!)
        (9.45, 77, 0.95, 0.17),  # F5
        (10.12, 81, 1.85, 0.20), # A5 (golden sunbeam bloom!)
        (10.68, 84, 1.80, 0.19), # C6 (shimmering resolution)
    ]

    for t0, midi, dur, gain in melody:
        tone = synth_celesta(midi_to_freq(midi), dur)
        add_stereo(buf_l, buf_r, t0, tone, gain=gain, pan=0.14)


# =============================================================================
# 4. STEREO REVERB & MASTERING
# =============================================================================

def apply_stereo_reverb(buf_l, buf_r, wet: float = 0.24):
    """Simple, warm multi-tap stereo reverb tail."""
    taps_l = [(int(0.037 * SAMPLE_RATE), 0.38), (int(0.083 * SAMPLE_RATE), 0.26), (int(0.149 * SAMPLE_RATE), 0.16)]
    taps_r = [(int(0.043 * SAMPLE_RATE), 0.36), (int(0.097 * SAMPLE_RATE), 0.25), (int(0.167 * SAMPLE_RATE), 0.15)]
    out_l = list(buf_l)
    out_r = list(buf_r)
    for i in range(NUM_SAMPLES):
        rl = rr = 0.0
        for d, g in taps_l:
            if i >= d:
                rl += buf_l[i - d] * g + buf_r[i - d] * g * 0.25
        for d, g in taps_r:
            if i >= d:
                rr += buf_r[i - d] * g + buf_l[i - d] * g * 0.25
        out_l[i] = buf_l[i] * (1.0 - wet * 0.35) + rl * wet
        out_r[i] = buf_r[i] * (1.0 - wet * 0.35) + rr * wet
    return out_l, out_r


def main():
    print("[audio] Synthesizing 12.5s stereo soundtrack & ambient soundscape...")
    buf_l = [0.0] * NUM_SAMPLES
    buf_r = [0.0] * NUM_SAMPLES

    # 1. Babbling brook ambience
    generate_babbling_brook(buf_l, buf_r)

    # 2. Story-synced Foley SFX
    add_stereo(buf_l, buf_r, 1.54, synth_water_plop(0.28), gain=0.45, pan=-0.25)

    # Woodland songbirds (gentle, warm, far in the trees)
    bird1 = synth_songbird([(2250, 2950), (2800, 2400), (2550, 3200)], 0.12)
    bird2 = synth_songbird([(2600, 3350), (3100, 2750)], 0.13)
    add_stereo(buf_l, buf_r, 3.45, bird1, gain=0.14, pan=-0.58)
    add_stereo(buf_l, buf_r, 6.25, bird2, gain=0.12, pan=0.52)

    # Duckling gentle paddling & two adorable peeps
    for k in range(8):
        pt = 7.55 + k * 0.44
        add_stereo(buf_l, buf_r, pt, synth_paddle_splash(0.15, seed=300 + k), gain=0.14, pan=0.15)
    add_stereo(buf_l, buf_r, 8.42, synth_duckling_peep(680.0, 0.18), gain=0.30, pan=0.08)
    add_stereo(buf_l, buf_r, 9.52, synth_duckling_peep(735.0, 0.21), gain=0.32, pan=0.18)
    add_stereo(buf_l, buf_r, 8.95, synth_water_plop(0.22), gain=0.22, pan=0.15)

    # 3. Original Music Score
    compose_music(buf_l, buf_r)

    # 4. Warm Stereo Reverb
    buf_l, buf_r = apply_stereo_reverb(buf_l, buf_r, wet=0.24)

    # 5. Master fade-in/out, peak normalization & gentle soft-clip
    peak = max(max(abs(x) for x in buf_l), max(abs(x) for x in buf_r), 1e-6)
    target_gain = 0.86 / peak

    fade_in_n = int(0.45 * SAMPLE_RATE)
    fade_out_n = int(0.85 * SAMPLE_RATE)

    pcm = bytearray(NUM_SAMPLES * 4)
    for i in range(NUM_SAMPLES):
        env = 1.0
        if i < fade_in_n:
            env = i / fade_in_n
        elif i > NUM_SAMPLES - fade_out_n:
            env = (NUM_SAMPLES - i) / fade_out_n
        sl = math.tanh(buf_l[i] * target_gain * env * 1.05)
        sr = math.tanh(buf_r[i] * target_gain * env * 1.05)
        struct.pack_into("<hh", pcm, i * 4, int(clamp(sl) * 32767), int(clamp(sr) * 32767))

    with wave.open(OUT_PATH, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm)

    print(f"[audio] Saved {OUT_PATH} ({os.path.getsize(OUT_PATH) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
