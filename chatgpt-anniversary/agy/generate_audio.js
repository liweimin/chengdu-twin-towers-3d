// Original Beat-Synced Electronic Soundtrack Generator (128 BPM, 50.0s, 44.1kHz Stereo)
// Pure Node.js DSP — no external audio samples, 100% original composition.
const fs = require('fs');
const path = require('path');

const SAMPLE_RATE = 44100;
const BPM = 128;
const BEAT = 60 / BPM; // 0.46875s
const BAR = BEAT * 4;  // 1.875s
const DURATION = 50.0; // seconds
const NUM_SAMPLES = Math.floor(SAMPLE_RATE * DURATION);

const left = new Float32Array(NUM_SAMPLES);
const right = new Float32Array(NUM_SAMPLES);

// Utility: MIDI note to Hz
function mtof(midi) {
  return 440 * Math.pow(2, (midi - 69) / 12);
}

// Deterministic pseudo-random for crisp hi-hats / snares / noise risers
let seed = 133742;
function rand() {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return (seed / 4294967296) * 2 - 1;
}

// Soft saturation / warm analog clipping
function tanh(x) {
  return Math.tanh(x);
}

// Add mono/stereo signal safely with pan (-1 left, +1 right)
function addSample(idx, val, pan = 0) {
  if (idx < 0 || idx >= NUM_SAMPLES) return;
  const gL = Math.cos((pan + 1) * Math.PI * 0.25);
  const gR = Math.sin((pan + 1) * Math.PI * 0.25);
  left[idx] += val * gL;
  right[idx] += val * gR;
}

// 1. Punchy Electronic Kick
function synthKick(startTime, gain = 0.78) {
  const startIdx = Math.floor(startTime * SAMPLE_RATE);
  const len = Math.floor(0.32 * SAMPLE_RATE);
  let phase = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const freq = 48 + 135 * Math.exp(-t * 34);
    phase += (2 * Math.PI * freq) / SAMPLE_RATE;
    const env = Math.exp(-t * 11.5) * Math.min(1, t / 0.002);
    const click = Math.exp(-t * 180) * Math.sin(2 * Math.PI * 1600 * t) * 0.22;
    const s = tanh((Math.sin(phase) * env + click) * 1.35) * gain;
    addSample(startIdx + i, s, 0);
  }
}

// 2. Crisp Clap / Snare
function synthClap(startTime, gain = 0.42) {
  const startIdx = Math.floor(startTime * SAMPLE_RATE);
  const len = Math.floor(0.24 * SAMPLE_RATE);
  let lp = 0, hp = 0, prev = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const n = rand();
    // Bandpass-ish noise
    lp += 0.28 * (n - lp);
    hp = lp - prev;
    prev = lp * 0.85;
    // Multi-burst clap transient + snappy body
    const burst =
      (t < 0.012 ? 1.0 : 0) +
      (t >= 0.014 && t < 0.025 ? 0.85 : 0) +
      (t >= 0.027 ? Math.exp(-(t - 0.027) * 18) : 0);
    const body = Math.sin(2 * Math.PI * 195 * t) * Math.exp(-t * 28) * 0.32;
    const s = (hp * burst * 0.9 + body) * gain;
    addSample(startIdx + i, s, (i % 2 === 0 ? -0.06 : 0.06));
  }
}

// 3. Tight Hi-Hat (Closed / Open)
function synthHat(startTime, open = false, gain = 0.16, pan = 0.12) {
  const startIdx = Math.floor(startTime * SAMPLE_RATE);
  const dur = open ? 0.22 : 0.055;
  const len = Math.floor(dur * SAMPLE_RATE);
  let prev = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const n = rand();
    const hp = n - prev * 0.92;
    prev = n;
    const metal =
      Math.sin(2 * Math.PI * 5400 * t) * 0.12 +
      Math.sin(2 * Math.PI * 7820 * t) * 0.12;
    const env = Math.exp(-t * (open ? 14 : 68)) * Math.min(1, t / 0.0015);
    addSample(startIdx + i, (hp * 0.8 + metal) * env * gain, pan);
  }
}

// 4. Tactile Keystroke / UI Click (for Intro prompt typing)
function synthKeyClick(startTime, pitch = 2400, gain = 0.20, pan = 0) {
  const startIdx = Math.floor(startTime * SAMPLE_RATE);
  const len = Math.floor(0.03 * SAMPLE_RATE);
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const env = Math.exp(-t * 140);
    const s = (Math.sin(2 * Math.PI * pitch * t) * 0.6 + rand() * 0.4) * env * gain;
    addSample(startIdx + i, s, pan);
  }
}

// 5. Sub-Drop / Impact Boom (for major Act transitions)
function synthImpact(startTime, gain = 0.65) {
  const startIdx = Math.floor(startTime * SAMPLE_RATE);
  const len = Math.floor(1.4 * SAMPLE_RATE);
  let phase = 0, lp = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const freq = 34 + 62 * Math.exp(-t * 3.2);
    phase += (2 * Math.PI * freq) / SAMPLE_RATE;
    const sub = Math.sin(phase) * Math.exp(-t * 2.1) * Math.min(1, t / 0.008);
    lp += 0.06 * (rand() - lp);
    const air = lp * Math.exp(-t * 3.8) * 0.55;
    addSample(startIdx + i, (sub * 0.85 + air) * gain, 0);
  }
}

// 6. Noise Riser / Sweep (builds tension into drops)
function synthRiser(startTime, dur, gain = 0.24) {
  const startIdx = Math.floor(startTime * SAMPLE_RATE);
  const len = Math.floor(dur * SAMPLE_RATE);
  let lp = 0;
  for (let i = 0; i < len; i++) {
    const p = i / len;
    const t = i / SAMPLE_RATE;
    const cutoff = 0.015 + Math.pow(p, 2.4) * 0.45;
    const n = rand();
    lp += cutoff * (n - lp);
    const tone = Math.sin(2 * Math.PI * (220 + p * p * 1100) * t) * 0.16;
    const env = Math.pow(p, 2.1) * (p > 0.96 ? (1 - p) / 0.04 : 1);
    const pan = Math.sin(p * Math.PI * 4) * 0.35;
    addSample(startIdx + i, (lp + tone) * env * gain, pan);
  }
}

// 7. Punchy Pluck Bass (saw/triangle blend with resonant lowpass envelope)
function synthBass(startTime, dur, midi, gain = 0.34) {
  const startIdx = Math.floor(startTime * SAMPLE_RATE);
  const len = Math.floor(dur * SAMPLE_RATE);
  const freq = mtof(midi);
  let ph1 = 0, ph2 = 0, lp = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    ph1 = (ph1 + freq / SAMPLE_RATE) % 1;
    ph2 = (ph2 + (freq * 1.003) / SAMPLE_RATE) % 1;
    const saw = (ph1 * 2 - 1) * 0.5 + (ph2 * 2 - 1) * 0.5;
    const sub = Math.sin(2 * Math.PI * freq * t);
    const fEnv = 0.04 + 0.32 * Math.exp(-t * 14);
    lp += fEnv * (saw - lp);
    const amp = Math.min(1, t / 0.005) * Math.exp(-t * 4.5) * Math.min(1, (dur - t) / 0.015);
    addSample(startIdx + i, tanh((lp * 0.72 + sub * 0.55) * 1.2) * amp * gain, 0);
  }
}

// 8. Warm Lush Pad / Rhodes Chord
function synthPadChord(startTime, dur, midis, gain = 0.11, bright = 0.35) {
  const startIdx = Math.floor(startTime * SAMPLE_RATE);
  const len = Math.floor(dur * SAMPLE_RATE);
  const freqs = midis.map(mtof);
  const phases = freqs.map(() => Math.random() * Math.PI * 2);
  const phasesDet = freqs.map(() => Math.random() * Math.PI * 2);

  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const atk = Math.min(1, t / 0.18);
    const rel = Math.min(1, (dur - t) / 0.35);
    const env = atk * rel;
    // Sidechain pumping feel synced to quarter-note beats (only when beat > 8 and < 92)
    const globalT = startTime + t;
    const beatPos = (globalT / BEAT) % 1;
    const sc = (globalT >= 2 * BAR && globalT < 23 * BAR)
      ? 0.42 + 0.58 * Math.min(1, Math.pow(beatPos, 0.45))
      : 1.0;

    let sumL = 0, sumR = 0;
    for (let k = 0; k < freqs.length; k++) {
      phases[k] += (2 * Math.PI * freqs[k]) / SAMPLE_RATE;
      phasesDet[k] += (2 * Math.PI * freqs[k] * 1.0045) / SAMPLE_RATE;
      const v1 = Math.sin(phases[k]) + bright * 0.32 * Math.sin(phases[k] * 2) + bright * 0.14 * Math.sin(phases[k] * 3);
      const v2 = Math.sin(phasesDet[k]) + bright * 0.32 * Math.sin(phasesDet[k] * 2);
      const pan = (k / Math.max(1, freqs.length - 1)) * 1.2 - 0.6;
      sumL += (v1 * (0.5 - pan * 0.3) + v2 * (0.5 + pan * 0.3));
      sumR += (v2 * (0.5 - pan * 0.3) + v1 * (0.5 + pan * 0.3));
    }
    const idx = startIdx + i;
    if (idx >= 0 && idx < NUM_SAMPLES) {
      const g = (env * sc * gain) / Math.sqrt(freqs.length);
      left[idx] += sumL * g;
      right[idx] += sumR * g;
    }
  }
}

// 9. Sparkling Pluck / Arp Bell
function synthPluck(startTime, dur, midi, gain = 0.18, pan = 0) {
  const startIdx = Math.floor(startTime * SAMPLE_RATE);
  const len = Math.floor(dur * SAMPLE_RATE);
  const freq = mtof(midi);
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const env = Math.min(1, t / 0.004) * Math.exp(-t * 7.5);
    const fm = Math.sin(2 * Math.PI * freq * 2 * t) * Math.exp(-t * 16) * 1.4;
    const s = (Math.sin(2 * Math.PI * freq * t + fm) * 0.75 + Math.sin(2 * Math.PI * freq * 3 * t) * Math.exp(-t * 22) * 0.25) * env * gain;
    addSample(startIdx + i, s, pan);
  }
}

// 10. Soaring Lead Synth (for Act IV Climax)
function synthLead(startTime, dur, midi, gain = 0.19, pan = 0) {
  const startIdx = Math.floor(startTime * SAMPLE_RATE);
  const len = Math.floor(dur * SAMPLE_RATE);
  const freq = mtof(midi);
  let p1 = 0, p2 = 0, p3 = 0, lp = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const vib = 1 + 0.0035 * Math.sin(2 * Math.PI * 5.8 * t) * Math.min(1, t / 0.12);
    p1 = (p1 + (freq * vib) / SAMPLE_RATE) % 1;
    p2 = (p2 + (freq * vib * 1.006) / SAMPLE_RATE) % 1;
    p3 = (p3 + (freq * vib * 0.994) / SAMPLE_RATE) % 1;
    const raw = ((p1 * 2 - 1) + (p2 * 2 - 1) + (p3 * 2 - 1)) / 3;
    const cut = 0.12 + 0.25 * Math.exp(-t * 4.5);
    lp += cut * (raw - lp);
    const env = Math.min(1, t / 0.015) * Math.min(1, (dur - t) / 0.04);
    addSample(startIdx + i, lp * env * gain, pan);
  }
}

// ============================================================
// COMPOSITION — 26 Bars @ 128 BPM (48.75s + 1.25s tail = 50.0s)
// Progression: Dm9 -> Bbmaj7 -> Fmaj7 -> C6/9
// ============================================================
const CHORDS = [
  { root: 38, notes: [50, 53, 57, 60, 64] }, // Dm9
  { root: 34, notes: [46, 50, 53, 57, 62] }, // Bbmaj7
  { root: 41, notes: [53, 57, 60, 64, 67] }, // Fmaj7
  { root: 36, notes: [48, 52, 55, 57, 62] }, // C6/9
];

const ARP_PATTERNS = [
  [62, 65, 69, 72, 74, 72, 69, 65], // Dm
  [58, 62, 65, 69, 74, 69, 65, 62], // Bb
  [60, 65, 69, 72, 76, 72, 69, 65], // F
  [60, 64, 67, 72, 74, 72, 67, 64], // C
];

// Intro typing clicks (Bars 0–2, 0.0s - 3.75s)
const clickTimes = [0.25, 0.48, 0.72, 0.95, 1.18, 1.41, 1.64, 1.875, 2.11, 2.34, 2.58, 2.81, 3.05, 3.28, 3.52];
clickTimes.forEach((ct, i) => {
  synthKeyClick(ct, 2100 + (i % 4) * 280, 0.15 + i * 0.005, (i % 2 ? -0.18 : 0.18));
});
synthPadChord(0.0, 2 * BAR, CHORDS[0].notes, 0.10, 0.18);
synthRiser(1.875, 1.875, 0.20);

// Major Act impacts
synthImpact(2 * BAR, 0.68);   // Bar 2: 3.75s (2022 Launch!)
synthImpact(6 * BAR, 0.62);   // Bar 6: 11.25s (2024 GPT-4o!)
synthImpact(9 * BAR, 0.56);   // Bar 9: 16.875s (o1 Reasoning!)
synthImpact(12 * BAR, 0.72);  // Bar 12: 22.50s (2025 GPT-5!)
synthImpact(15 * BAR, 0.60);  // Bar 15: 28.125s (WAU Exponential!)
synthImpact(18 * BAR, 0.80);  // Bar 18: 33.75s (1.2B & GPT-6 Climax!)
synthImpact(23 * BAR, 0.65);  // Bar 23: 43.125s (Finale Resolve!)

// Risers before major drops
synthRiser(5 * BAR, BAR, 0.18);
synthRiser(11 * BAR, BAR, 0.24);
synthRiser(17 * BAR, BAR, 0.30);
synthRiser(22 * BAR, BAR, 0.22);

// Main Groove Loop: Bars 2 to 22 (3.75s to 43.125s)
for (let bar = 2; bar < 23; bar++) {
  const barStart = bar * BAR;
  const chordIdx = (bar - 2) % 4;
  const chord = CHORDS[chordIdx];
  const arp = ARP_PATTERNS[chordIdx];
  const isClimax = bar >= 18;
  const isAct3 = bar >= 12 && bar < 18;
  const isAct2 = bar >= 6 && bar < 12;

  // Lush Pad every bar
  synthPadChord(barStart, BAR * 1.02, chord.notes, isClimax ? 0.14 : 0.11, isClimax ? 0.65 : isAct3 ? 0.5 : 0.3);

  // Drums
  for (let b = 0; b < 4; b++) {
    const t = barStart + b * BEAT;
    // Skip kick on beat 3.5 of riser bar 17 for dramatic drop
    if (!(bar === 17 && b === 3)) {
      synthKick(t, isClimax ? 0.84 : 0.75);
    }
    if (b === 1 || b === 3) {
      synthClap(t, isClimax ? 0.46 : 0.38);
    }
    // Off-beat open hat + 16th closed hats
    synthHat(t + BEAT * 0.5, true, isClimax ? 0.19 : 0.14, 0.18);
    synthHat(t + BEAT * 0.25, false, 0.09, -0.22);
    if (isAct3 || isClimax) {
      synthHat(t + BEAT * 0.75, false, 0.11, 0.26);
    }
  }

  // Snare roll fill on bar 17 (last 2 beats)
  if (bar === 17) {
    for (let s = 0; s < 8; s++) {
      synthClap(barStart + 2 * BEAT + s * (BEAT * 0.25), 0.18 + s * 0.04);
    }
  }

  // Driving syncopated bassline
  const bassPattern = [0, 0.75, 1.5, 2.0, 2.75, 3.5];
  bassPattern.forEach((bp, idx) => {
    const note = chord.root + (idx === 5 ? 12 : 0);
    synthBass(barStart + bp * BEAT, BEAT * 0.62, note, isClimax ? 0.38 : 0.32);
  });

  // Sparkling 8th-note Arp
  for (let step = 0; step < 8; step++) {
    const t = barStart + step * (BEAT * 0.5);
    const note = arp[step] + (isClimax && step % 2 === 1 ? 12 : 0);
    const pan = Math.sin((bar * 8 + step) * 0.6) * 0.45;
    synthPluck(t, BEAT * 0.7, note, isAct2 || isAct3 || isClimax ? 0.16 : 0.12, pan);
  }
}

// Soaring Melodic Hook for Act III (Bars 12–17) & Peak Climax Act IV (Bars 18–22)
const MELODY_4BAR = [
  // Bar 0 (Dm9)
  [0.0, 0.75, 74], [0.75, 0.75, 77], [1.5, 1.0, 81], [2.5, 0.5, 79], [3.0, 1.0, 77],
  // Bar 1 (Bbmaj7)
  [4.0, 0.75, 74], [4.75, 0.75, 77], [5.5, 1.5, 79], [7.0, 1.0, 77],
  // Bar 2 (Fmaj7)
  [8.0, 0.75, 81], [8.75, 0.75, 84], [9.5, 1.0, 86], [10.5, 0.5, 84], [11.0, 1.0, 81],
  // Bar 3 (C6/9)
  [12.0, 1.5, 79], [13.5, 0.5, 77], [14.0, 1.0, 76], [15.0, 1.0, 74],
];

// Play hook at Bar 12 (warm octave) and Bar 18 (soaring full climax!)
MELODY_4BAR.forEach(([bOff, bDur, midi]) => {
  synthLead(12 * BAR + bOff * BEAT, bDur * BEAT * 0.95, midi, 0.14, -0.15);
  synthLead(18 * BAR + bOff * BEAT, bDur * BEAT * 0.95, midi, 0.19, 0.15);
  synthPluck(18 * BAR + bOff * BEAT, bDur * BEAT * 1.1, midi + 12, 0.11, -0.25);
});
// Final triumphant lift on Bar 22
synthLead(22 * BAR, 2 * BEAT, 86, 0.21, 0);
synthLead(22 * BAR + 2 * BEAT, 2 * BEAT, 88, 0.22, 0);

// Outro Resolution (Bars 23–26, 43.125s - 50.0s): Warm Fmaj9 glow + heartbeat
synthPadChord(23 * BAR, 6.2, [41, 53, 57, 60, 64, 67, 72], 0.18, 0.28);
synthKick(23 * BAR, 0.65);
synthKick(24 * BAR, 0.50);
synthKick(25 * BAR, 0.35);
[72, 76, 79, 84, 88].forEach((m, i) => {
  synthPluck(23 * BAR + i * BEAT * 0.75, 2.2, m, 0.14 - i * 0.015, (i - 2) * 0.25);
});

// Simple Stereo Delay (dotted 8th = 0.75 * BEAT) for lush studio space
const delaySamplesL = Math.floor(BEAT * 0.75 * SAMPLE_RATE);
const delaySamplesR = Math.floor(BEAT * 0.50 * SAMPLE_RATE);
for (let i = 0; i < NUM_SAMPLES; i++) {
  if (i >= delaySamplesL) left[i] += right[i - delaySamplesL] * 0.18;
  if (i >= delaySamplesR) right[i] += left[i - delaySamplesR] * 0.16;
}

// Master Limiter + Smooth Fade Out (last 1.8s)
const fadeStart = Math.floor((DURATION - 1.8) * SAMPLE_RATE);
let peak = 0.0001;
for (let i = 0; i < NUM_SAMPLES; i++) {
  let l = left[i], r = right[i];
  if (i >= fadeStart) {
    const f = Math.max(0, 1 - (i - fadeStart) / (NUM_SAMPLES - fadeStart));
    const smooth = f * f;
    l *= smooth;
    r *= smooth;
  }
  l = tanh(l * 1.12);
  r = tanh(r * 1.12);
  left[i] = l;
  right[i] = r;
  const m = Math.max(Math.abs(l), Math.abs(r));
  if (m > peak) peak = m;
}
const norm = 0.94 / peak;

// Write 16-bit Stereo WAV
const dataSize = NUM_SAMPLES * 4;
const buf = Buffer.alloc(44 + dataSize);
buf.write('RIFF', 0);
buf.writeUInt32LE(36 + dataSize, 4);
buf.write('WAVE', 8);
buf.write('fmt ', 12);
buf.writeUInt32LE(16, 16);
buf.writeUInt16LE(1, 20); // PCM
buf.writeUInt16LE(2, 22); // Stereo
buf.writeUInt32LE(SAMPLE_RATE, 24);
buf.writeUInt32LE(SAMPLE_RATE * 4, 28);
buf.writeUInt16LE(4, 32);
buf.writeUInt16LE(16, 34);
buf.write('data', 36);
buf.writeUInt32LE(dataSize, 40);

let offset = 44;
for (let i = 0; i < NUM_SAMPLES; i++) {
  const sL = Math.max(-1, Math.min(1, left[i] * norm));
  const sR = Math.max(-1, Math.min(1, right[i] * norm));
  buf.writeInt16LE(Math.round(sL * 32767), offset);
  buf.writeInt16LE(Math.round(sR * 32767), offset + 2);
  offset += 4;
}

const outPath = path.join(__dirname, 'soundtrack.wav');
fs.writeFileSync(outPath, buf);
console.log(`Generated ${outPath} (${DURATION}s, ${BPM} BPM, ${(buf.length / 1024 / 1024).toFixed(2)} MB)`);
