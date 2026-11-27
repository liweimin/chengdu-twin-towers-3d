// generate_audio.mjs
// Original 30-second pastoral watercolor film score + natural creek soundscape + foley
// 48kHz 16-bit Stereo WAV synthesized with felt-piano, acoustic harp/guitar, celesta,
// warm chamber strings, stereo Schroeder hall reverb, babbling creek, birdsong & duckling chirps!

import fs from 'node:fs';
import path from 'node:path';

const SR = 48000;
const DUR = 30.2;
const N = Math.floor(SR * DUR);

const L = new Float32Array(N);
const R = new Float32Array(N);
const revL = new Float32Array(N);
const revR = new Float32Array(N);

// Deterministic PRNG
let seed = 20261127;
function rand() {
  seed = (seed + 0x6D2B79F5) >>> 0;
  let t = Math.imul(seed ^ (seed >>> 15), seed | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}

function midiToFreq(m) {
  return 440 * Math.pow(2, (m - 69) / 12);
}

// Mix helper with stereo pan (-1..+1) and reverb send
function addSample(idx, val, pan = 0, revSend = 0.35) {
  if (idx < 0 || idx >= N) return;
  const gL = Math.cos((pan + 1) * Math.PI * 0.25);
  const gR = Math.sin((pan + 1) * Math.PI * 0.25);
  L[idx] += val * gL;
  R[idx] += val * gR;
  revL[idx] += val * gL * revSend;
  revR[idx] += val * gR * revSend;
}

// 1. Warm Felt Piano (intimate, soft-hammered Ghibli watercolor tone!)
function playFeltPiano(timeSec, midi, dur = 2.6, vel = 0.32, pan = 0) {
  const f0 = midiToFreq(midi);
  const start = Math.floor(timeSec * SR);
  const len = Math.floor(dur * SR);
  const detune = 1.0007;
  for (let i = 0; i < len && start + i < N; i++) {
    const t = i / SR;
    const attack = Math.min(1, t / 0.018);
    const env = attack * (0.68 * Math.exp(-t * 1.45) + 0.32 * Math.exp(-t * 0.55));
    // Warm felted harmonics (rich fundamental + 2nd + gentle 3rd, minimal harsh high partials)
    let s =
      0.56 * Math.sin(2 * Math.PI * f0 * t) +
      0.24 * Math.sin(2 * Math.PI * f0 * detune * t + 0.2) +
      0.16 * Math.sin(2 * Math.PI * f0 * 2 * t) * Math.exp(-t * 1.8) +
      0.06 * Math.sin(2 * Math.PI * f0 * 3 * t) * Math.exp(-t * 3.0) +
      0.02 * Math.sin(2 * Math.PI * f0 * 4 * t) * Math.exp(-t * 4.5);
    // Tiny soft felt-hammer thump on attack
    if (t < 0.025) s += (rand() - 0.5) * 0.04 * Math.exp(-t * 180);
    addSample(start + i, s * env * vel, pan, 0.45);
  }
}

// 2. Warm Plucked Acoustic Guitar / Folk Harp
function playPluck(timeSec, midi, dur = 1.8, vel = 0.20, pan = 0) {
  const f0 = midiToFreq(midi);
  const start = Math.floor(timeSec * SR);
  const len = Math.floor(dur * SR);
  for (let i = 0; i < len && start + i < N; i++) {
    const t = i / SR;
    const attack = Math.min(1, t / 0.008);
    const env = attack * Math.exp(-t * 2.1);
    const s =
      0.62 * Math.sin(2 * Math.PI * f0 * t) +
      0.26 * Math.sin(2 * Math.PI * f0 * 2 * t + 0.4) * Math.exp(-t * 2.5) +
      0.10 * Math.sin(2 * Math.PI * f0 * 3 * t) * Math.exp(-t * 4.2) +
      0.04 * Math.sin(2 * Math.PI * f0 * 4 * t) * Math.exp(-t * 6.0);
    addSample(start + i, s * env * vel, pan, 0.42);
  }
}

// 3. Crystalline Celesta / Music-Box Sparkle
function playCelesta(timeSec, midi, dur = 2.2, vel = 0.16, pan = 0) {
  const f0 = midiToFreq(midi);
  const start = Math.floor(timeSec * SR);
  const len = Math.floor(dur * SR);
  for (let i = 0; i < len && start + i < N; i++) {
    const t = i / SR;
    const attack = Math.min(1, t / 0.004);
    const env = attack * Math.exp(-t * 1.9);
    const s =
      0.72 * Math.sin(2 * Math.PI * f0 * t) +
      0.20 * Math.sin(2 * Math.PI * f0 * 2.002 * t) * Math.exp(-t * 2.8) +
      0.08 * Math.sin(2 * Math.PI * f0 * 4.01 * t) * Math.exp(-t * 6.5);
    addSample(start + i, s * env * vel, pan, 0.62);
  }
}

// 4. Warm Airy Chamber Strings Pad (PROPER phase-accumulated vibrato => ZERO buzzing!)
function playStringNote(timeSec, midi, dur = 4.0, vel = 0.085, pan = 0) {
  const f0 = midiToFreq(midi);
  const start = Math.floor(timeSec * SR);
  const len = Math.floor(dur * SR);
  let ph1 = 0, ph2 = 0.7;
  let lp = 0;
  for (let i = 0; i < len && start + i < N; i++) {
    const t = i / SR;
    const u = t / dur;
    const env = Math.sin(Math.min(1, u * 2.5) * Math.PI * 0.5) * Math.sin(Math.min(1, (1 - u) * 2.2) * Math.PI * 0.5);
    const vib = 1 + 0.0016 * Math.sin(2 * Math.PI * 4.5 * t) * Math.min(1, t / 1.0);
    ph1 += (2 * Math.PI * f0 * vib) / SR;
    ph2 += (2 * Math.PI * f0 * 1.0022 * vib) / SR;
    // Pure, warm, silky high-register string tone (no harsh buzzing harmonics!)
    const raw =
      0.60 * Math.sin(ph1) +
      0.26 * Math.sin(ph2) +
      0.11 * Math.sin(ph1 * 2) +
      0.03 * Math.sin(ph1 * 3);
    // Gentle warm low-pass smoothing
    lp += 0.14 * (raw - lp);
    addSample(start + i, lp * env * vel, pan, 0.65);
  }
}

// ============================================================================
// ORIGINAL SCORE COMPOSITION: "The Story of a Paper Boat" (Key of F Major, 72 BPM)
// ============================================================================
const beat = 60 / 72; // 0.8333s per beat

// Gentle guitar/harp flowing water arpeggios across the 4 musical chapters
const chordProg = [
  // Shot 1 (0..7.5s): Warm, sunlit Fmaj7 -> Dm9 -> Bbmaj7 -> C9sus4
  { t: 0.0, notes: [53, 60, 64, 69], bass: 41 },
  { t: 2.0, notes: [50, 57, 60, 64], bass: 38 },
  { t: 4.0, notes: [46, 53, 57, 62], bass: 46 },
  { t: 6.0, notes: [48, 55, 58, 62], bass: 48 },
  // Shot 2 (7.5..14.5s): Shaded, reflective Dm7 -> Am7 -> Gm9 -> C7sus4
  { t: 8.0, notes: [50, 57, 60, 65], bass: 50 },
  { t: 10.0, notes: [45, 52, 55, 60], bass: 45 },
  { t: 12.0, notes: [43, 50, 53, 57], bass: 43 },
  // Shot 3 (14.5..22.5s): Curious & heartwarming Bbmaj7 -> C6 -> Fmaj9 -> Dm7 -> Bbmaj7 -> C9
  { t: 14.4, notes: [46, 53, 57, 62], bass: 46 },
  { t: 16.4, notes: [48, 55, 57, 64], bass: 48 },
  { t: 18.6, notes: [53, 60, 64, 67], bass: 41 }, // Radiant harmonic bloom on the duckling's nudge!
  { t: 20.6, notes: [50, 57, 62, 64], bass: 50 },
  // Shot 4 (22.5..30.0s): Expansive golden horizon Bbmaj7 -> C9 -> Fmaj9 (warm resolution!)
  { t: 22.6, notes: [46, 53, 57, 62], bass: 46 },
  { t: 24.6, notes: [48, 55, 60, 64], bass: 48 },
  { t: 26.6, notes: [53, 60, 64, 69], bass: 41 },
];

for (const ch of chordProg) {
  playFeltPiano(ch.t, ch.bass, 3.2, 0.22, -0.25);
  ch.notes.forEach((m, idx) => {
    playPluck(ch.t + idx * 0.28, m, 2.0, 0.13, -0.35 + idx * 0.24);
  });
}

// Expressive Felt-Piano & Celesta Melody synced to story beats!
const melody = [
  // Shot 1: Gentle launch melody (0.6s..7.0s)
  [0.6, 69, 1.6, 0.24], [1.6, 72, 1.2, 0.22], [2.15, 76, 2.4, 0.28], // Touchdown shimmer!
  [3.4, 74, 1.4, 0.22], [4.2, 72, 1.6, 0.22], [5.2, 69, 1.8, 0.21], [6.2, 67, 2.2, 0.20],

  // Shot 2: Quiet shaded eddy contemplation (8.2s..13.6s)
  [8.2, 65, 1.8, 0.19], [9.4, 69, 1.6, 0.19], [10.4, 67, 2.0, 0.18],
  [11.8, 64, 1.8, 0.17], [12.9, 62, 2.2, 0.16],

  // Shot 3: Playful duckling arrival & heartwarming nudge bloom! (14.8s..22.0s)
  [14.8, 69, 0.9, 0.21], [15.4, 72, 0.9, 0.22], [16.0, 74, 1.4, 0.23],
  [17.0, 72, 1.0, 0.20], [17.7, 69, 1.0, 0.18],
  // 18.6s NUDGE BLOOM!
  [18.6, 76, 2.2, 0.28], [19.6, 77, 1.4, 0.25], [20.4, 79, 2.0, 0.27], [21.5, 76, 1.8, 0.24],

  // Shot 4: Soaring poetic golden horizon resolution (22.6s..28.5s)
  [22.6, 74, 1.8, 0.26], [23.8, 72, 1.6, 0.24], [24.8, 76, 2.2, 0.26],
  [26.0, 74, 1.6, 0.23], [26.8, 72, 3.2, 0.26], [27.8, 69, 3.0, 0.22],
];

for (const [t, m, d, v] of melody) {
  playFeltPiano(t, m, d, v, 0.15);
  // Add sparkling celesta harmonic halo on key magical moments (touchdown, nudge, sunlight finale!)
  if (t === 2.15 || t >= 18.6) {
    playCelesta(t + 0.02, m + 12, d * 1.1, v * 0.45, 0.35);
  }
}

// Soft, airy, high-register chamber strings shimmering gently from Shot 3's nudge through the golden finale
// (Zero muddy low drones — pure warm sunlit air supporting the felt piano & celesta!)
playStringNote(18.5, 65, 4.8, 0.065, -0.35); // F4 warm violin
playStringNote(18.6, 69, 4.8, 0.060, 0.35);  // A4
playStringNote(22.4, 62, 4.6, 0.065, -0.38); // D4
playStringNote(22.6, 69, 4.6, 0.058, 0.35);  // A4
playStringNote(25.6, 65, 4.4, 0.068, -0.32); // F4 warm resolution
playStringNote(25.6, 72, 4.4, 0.058, 0.32);  // C5
playStringNote(25.8, 76, 4.2, 0.045, 0.42);  // E5 (airy Fmaj7 golden shimmer!)

// ============================================================================
// NATURAL SOUNDSCAPE & FOLEY (Babbling Creek, Birdsong, Touchdown Plop, Duckling!)
// ============================================================================

// 1. Soothing Stereo Flowing Creek (0.0s .. 30.2s)
let lpL1 = 0, lpL2 = 0, lpR1 = 0, lpR2 = 0;
for (let i = 0; i < N; i++) {
  const t = i / SR;
  const fade = Math.min(1, t / 1.5) * Math.min(1, Math.max(0, (DUR - t) / 2.2));
  const wL = rand() * 2 - 1;
  const wR = rand() * 2 - 1;
  // Soft warm water band-pass (~300Hz..1400Hz) with slow organic eddy modulation
  lpL1 += 0.095 * (wL - lpL1);
  lpL2 += 0.018 * (lpL1 - lpL2);
  lpR1 += 0.095 * (wR - lpR1);
  lpR2 += 0.018 * (lpR1 - lpR2);
  const eddyL = 0.72 + 0.28 * Math.sin(t * 0.85) * Math.cos(t * 0.37);
  const eddyR = 0.72 + 0.28 * Math.cos(t * 0.78 + 0.8) * Math.sin(t * 0.41);
  const waterGain = 0.055 * fade;
  L[i] += (lpL1 - lpL2) * eddyL * waterGain;
  R[i] += (lpR1 - lpR2) * eddyR * waterGain;
}

// Subtle randomized babbling water droplets along the stream
for (let d = 0; d < 65; d++) {
  const t0 = rand() * 28.5 + 0.5;
  const fStart = 550 + rand() * 900;
  const pan = rand() * 1.4 - 0.7;
  const stIdx = Math.floor(t0 * SR);
  const dLen = Math.floor(0.055 * SR);
  for (let i = 0; i < dLen && stIdx + i < N; i++) {
    const t = i / SR;
    const f = fStart * (1 + t * 8.5); // upward bubble chirp
    const env = Math.sin((i / dLen) * Math.PI) * Math.exp(-t * 48);
    addSample(stIdx + i, Math.sin(2 * Math.PI * f * t) * env * 0.022, pan, 0.2);
  }
}

// 2. Paper Boat Touchdown Soft Water Plop (t = 2.12s)
{
  const stIdx = Math.floor(2.12 * SR);
  const dLen = Math.floor(0.18 * SR);
  for (let i = 0; i < dLen; i++) {
    const t = i / SR;
    const f = 310 + t * 1250;
    const env = Math.min(1, t / 0.008) * Math.exp(-t * 24);
    addSample(stIdx + i, Math.sin(2 * Math.PI * f * t) * env * 0.14, 0.1, 0.35);
  }
}

// 3. Distant Summer Birdsong (delicate FM warbler chirps at 4.5s, 13.0s, 24.4s)
function addBirdChirp(tStart, pan) {
  const notes = [
    [0.0, 2950, 3650, 0.11],
    [0.16, 3350, 2800, 0.09],
    [0.32, 3100, 3900, 0.14],
  ];
  for (const [dt, f1, f2, dur] of notes) {
    const stIdx = Math.floor((tStart + dt) * SR);
    const len = Math.floor(dur * SR);
    let ph = 0;
    for (let i = 0; i < len && stIdx + i < N; i++) {
      const u = i / len;
      const f = f1 + (f2 - f1) * Math.sin(u * Math.PI * 0.5) + Math.sin(u * Math.PI * 6) * 45;
      ph += (2 * Math.PI * f) / SR;
      const env = Math.sin(u * Math.PI) * 0.032;
      addSample(stIdx + i, Math.sin(ph) * env, pan, 0.65);
    }
  }
}
addBirdChirp(4.5, 0.65);
addBirdChirp(13.0, -0.55);
addBirdChirp(24.4, 0.50);

// 4. Authentic Cute Baby Duckling "Quack-Quack!" (Formant-filtered nasal bill resonance!)
//    Uses a rich glottal pulse train swept through two moving bandpass formants (F1: 950->1600->850Hz, F2: 2300Hz)
function addDucklingQuack(tStart, opts = {}) {
  const { dur = 0.21, pitch = 1.0, vol = 0.30, pan = -0.15 } = opts;
  const stIdx = Math.floor(tStart * SR);
  const len = Math.floor(dur * SR);
  let ph = 0;

  // Two biquad bandpass filter states for realistic duckling nasal bill formants
  let x1_1 = 0, x2_1 = 0, y1_1 = 0, y2_1 = 0;
  let x1_2 = 0, x2_2 = 0, y1_2 = 0, y2_2 = 0;

  for (let i = 0; i < len && stIdx + i < N; i++) {
    const u = i / len;
    // Cute baby-duckling pitch inflection: rises then dips gently
    const f0 = (360 + 135 * Math.sin(Math.pow(u, 0.75) * Math.PI) - 75 * u) * pitch;
    ph += f0 / SR;
    if (ph >= 1) ph -= 1;

    // Band-limited-ish warm glottal pulse (nasal buzz source)
    const src = (ph < 0.28 ? Math.sin((ph / 0.28) * Math.PI) : -0.35 * Math.sin(((ph - 0.28) / 0.72) * Math.PI))
              + 0.18 * (2 * ph - 1);

    // Moving Formant 1 (the unmistakable "quaa-ack / 嘎" vowel sweep!)
    const f1 = (920 + 720 * Math.sin(Math.pow(u, 0.65) * Math.PI)) * (0.9 + 0.1 * pitch);
    const w1 = (2 * Math.PI * f1) / SR;
    const alpha1 = Math.sin(w1) / (2 * 4.2);
    const b0_1 = alpha1, b2_1 = -alpha1, a0_1 = 1 + alpha1, a1_1 = -2 * Math.cos(w1), a2_1 = 1 - alpha1;
    const out1 = (b0_1 * src + b2_1 * x2_1 - a1_1 * y1_1 - a2_1 * y2_1) / a0_1;
    x2_1 = x1_1; x1_1 = src; y2_1 = y1_1; y1_1 = out1;

    // Formant 2 (cute bright baby-duckling bill resonance ~2350Hz)
    const f2 = (2250 + 420 * Math.sin(u * Math.PI)) * (0.92 + 0.08 * pitch);
    const w2 = (2 * Math.PI * f2) / SR;
    const alpha2 = Math.sin(w2) / (2 * 5.0);
    const b0_2 = alpha2, b2_2 = -alpha2, a0_2 = 1 + alpha2, a1_2 = -2 * Math.cos(w2), a2_2 = 1 - alpha2;
    const out2 = (b0_2 * src + b2_2 * x2_2 - a1_2 * y1_2 - a2_2 * y2_2) / a0_2;
    x2_2 = x1_2; x1_2 = src; y2_2 = y1_2; y1_2 = out2;

    // Crisp expressive amplitude envelope (quick beak-open attack, soft natural decay)
    const env = Math.min(1, u / 0.10) * Math.pow(1 - u, 0.72);
    const sig = (out1 * 1.45 + out2 * 0.75) * env * vol;
    addSample(stIdx + i, sig, pan, 0.34);
  }
}

// Duckling sound moments timed cleanly around voiceover & animation!
// 1) Shot 3 entrance (14.65s): cheerful playful "嘎、嘎！" as duckling swims out from reeds
addDucklingQuack(14.62, { dur: 0.17, pitch: 1.12, vol: 0.34, pan: -0.35 });
addDucklingQuack(14.88, { dur: 0.19, pitch: 1.05, vol: 0.36, pan: -0.28 });

// 2) Shot 3 curious head-tilt (17.25s): cute tiny inquisitive "嘎？" (rising pitch)
addDucklingQuack(17.25, { dur: 0.16, pitch: 1.18, vol: 0.28, pan: -0.18 });

// 3) Shot 3 tender nudge moment (18.52s): affectionate bright "嘎—嘎！" + gentle water nudge splash!
addDucklingQuack(18.50, { dur: 0.21, pitch: 1.02, vol: 0.42, pan: -0.08 });
addDucklingQuack(18.80, { dur: 0.18, pitch: 1.14, vol: 0.34, pan: -0.05 });

// Soft water nudge ripple plop at 18.60s
{
  const stIdx = Math.floor(18.60 * SR);
  const dLen = Math.floor(0.16 * SR);
  for (let i = 0; i < dLen; i++) {
    const t = i / SR;
    const f = 340 + t * 1100;
    const env = Math.min(1, t / 0.008) * Math.exp(-t * 24);
    addSample(stIdx + i, Math.sin(2 * Math.PI * f * t) * env * 0.13, 0.05, 0.30);
  }
}

// 4) Shot 4 gentle farewell (27.15s, right after final voiceover finishes): soft warm distant "嘎~" from left bank!
addDucklingQuack(27.15, { dur: 0.22, pitch: 1.06, vol: 0.24, pan: -0.45 });

// ============================================================================
// LUSH STEREO SCHROEDER HALL REVERB (Makes felt piano & strings sound studio-recorded!)
// ============================================================================
function applyComb(input, delayMs, fb) {
  const d = Math.floor((delayMs / 1000) * SR);
  const out = new Float32Array(N);
  let lp = 0;
  for (let i = d; i < N; i++) {
    const delayed = out[i - d];
    lp += 0.38 * (delayed - lp); // warm hall damping
    out[i] = input[i] + lp * fb;
  }
  return out;
}

const combL1 = applyComb(revL, 31.3, 0.76);
const combL2 = applyComb(revL, 37.9, 0.74);
const combL3 = applyComb(revL, 43.1, 0.72);
const combR1 = applyComb(revR, 33.7, 0.76);
const combR2 = applyComb(revR, 40.3, 0.74);
const combR3 = applyComb(revR, 46.7, 0.72);

for (let i = 0; i < N; i++) {
  const wetL = (combL1[i] + combL2[i] + combL3[i]) * 0.22;
  const wetR = (combR1[i] + combR2[i] + combR3[i]) * 0.22;
  // Gentle master fade-in (0.4s) & fade-out (2.0s)
  const t = i / SR;
  const mFade = Math.min(1, t / 0.4) * Math.min(1, Math.max(0, (DUR - t) / 2.0));
  L[i] = Math.tanh((L[i] + wetL) * 0.92) * mFade;
  R[i] = Math.tanh((R[i] + wetR) * 0.92) * mFade;
}

// Write 48kHz 16-bit Stereo WAV
function writeWav(filePath, left, right, sr) {
  const numSamples = left.length;
  const dataBytes = numSamples * 4;
  const buf = Buffer.alloc(44 + dataBytes);
  buf.write('RIFF', 0);
  buf.writeUInt32LE(36 + dataBytes, 4);
  buf.write('WAVE', 8);
  buf.write('fmt ', 12);
  buf.writeUInt32LE(16, 16);
  buf.writeUInt16LE(1, 20); // PCM
  buf.writeUInt16LE(2, 22); // Stereo
  buf.writeUInt32LE(sr, 24);
  buf.writeUInt32LE(sr * 4, 28);
  buf.writeUInt16LE(4, 32);
  buf.writeUInt16LE(16, 34);
  buf.write('data', 36);
  buf.writeUInt32LE(dataBytes, 40);
  let off = 44;
  for (let i = 0; i < numSamples; i++) {
    const sL = Math.max(-1, Math.min(1, left[i]));
    const sR = Math.max(-1, Math.min(1, right[i]));
    buf.writeInt16LE(Math.round(sL * 32767), off);
    buf.writeInt16LE(Math.round(sR * 32767), off + 2);
    off += 4;
  }
  fs.writeFileSync(filePath, buf);
}

const outDir = path.join(process.cwd(), 'audio');
fs.mkdirSync(outDir, { recursive: true });
const outWav = path.join(outDir, 'score_and_foley.wav');
writeWav(outWav, L, R, SR);
console.log(`Generated original 30s stereo soundtrack & soundscape: ${outWav} (${(fs.statSync(outWav).size / 1024 / 1024).toFixed(2)} MB)`);
