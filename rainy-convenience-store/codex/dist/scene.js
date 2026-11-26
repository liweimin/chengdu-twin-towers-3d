const scene = document.querySelector(".scene");
const art = document.querySelector(".scene-art");
const sign = document.querySelector(".sign");
const signFace = document.querySelector(".sign-face");
const canvas = document.querySelector(".weather");
const paint = canvas.getContext("2d");
const portrait = matchMedia("(max-aspect-ratio: 14/11)");
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
const random = (low, high) => low + Math.random() * (high - low);

const pointer = { x: 0, y: 0 };
const pan = { x: 0, y: 0 };
const glass = [];
const ripples = [];
let rain = [];
let width = 0;
let height = 0;
let artWidth = 0;
let artHeight = 0;
let artLeft = 0;
let artTop = 0;
let lastFrame = 0;
let frame = 0;
let nextDrip = 1;
let nextRipple = 0;
let flicker;

const rainLayers = [
  { density: 15500, speed: [82, 150], length: [5, 12], opacity: [0.03, 0.15], depth: 0.4, stroke: 0.7 },
  { density: 21200, speed: [156, 262], length: [9, 20], opacity: [0.06, 0.23], depth: 1, stroke: 0.9 },
  { density: 65000, speed: [276, 410], length: [15, 29], opacity: [0.08, 0.24], depth: 1.7, stroke: 1.1 },
];

function resize() {
  width = scene.clientWidth;
  height = scene.clientHeight;
  const bounds = art.getBoundingClientRect();
  artWidth = bounds.width;
  artHeight = bounds.height;
  artLeft = bounds.left + pan.x * 8;
  artTop = bounds.top + pan.y * 5;

  const scale = Math.min(devicePixelRatio || 1, 1.5);
  canvas.width = Math.round(width * scale);
  canvas.height = Math.round(height * scale);
  paint.setTransform(scale, 0, 0, scale, 0, 0);

  rain = rainLayers.flatMap((layer) => {
    const count = Math.min(125, Math.max(7, Math.round(width * height / layer.density)));
    return Array.from({ length: count }, () => ({
      x: random(0, width),
      y: random(0, height),
      speed: random(...layer.speed),
      length: random(...layer.length),
      opacity: random(...layer.opacity),
      depth: layer.depth,
      stroke: layer.stroke,
    }));
  });
  glass.length = 0;
  ripples.length = 0;
  if (reducedMotion.matches || document.hidden) paint.clearRect(0, 0, width, height);
  else if (!frame) frame = requestAnimationFrame(draw);
}

function drawRain(step) {
  paint.strokeStyle = "#b1c7da";
  for (const drop of rain) {
    drop.x -= drop.speed * 0.10 * step;
    drop.y += drop.speed * step;
    if (drop.y > height + 45 || drop.x < -40) {
      drop.x = random(0, width + 32);
      drop.y = random(-65, -35);
    }

    const x = drop.x + pan.x * 14 * drop.depth;
    const y = drop.y + pan.y * 9 * drop.depth;
    paint.globalAlpha = drop.opacity;
    paint.lineWidth = drop.stroke;
    paint.beginPath();
    paint.moveTo(x, y);
    paint.lineTo(x + drop.length * 0.10, y - drop.length);
    paint.stroke();
  }
}

function drawGlass(step) {
  nextDrip -= step;
  if (nextDrip <= 0) {
    glass.push({
      x: random(0.04, 0.96) * width,
      y: random(-0.06, 0.34) * height,
      speed: random(38, 69),
      sway: random(0, Math.PI * 2),
      age: 0,
      life: random(2.6, 4.6),
    });
    nextDrip = random(0.9, 2.5);
  }

  for (let i = glass.length - 1; i >= 0; i--) {
    const drop = glass[i];
    drop.age += step;
    if (drop.age >= drop.life || drop.y > height + 24) {
      glass.splice(i, 1);
      continue;
    }
    drop.y += drop.speed * (1 + 0.20 * Math.sin(drop.age * 3.3 + drop.sway)) * step;

    const x = drop.x + 2.2 * Math.sin(drop.age * 1.8 + drop.sway) + pan.x * 34;
    const y = drop.y + pan.y * 23;
    const tail = Math.min(39, drop.age * 19);
    const fade = Math.min(1, drop.age * 1.9, (drop.life - drop.age) * 1.6);
    const trail = paint.createLinearGradient(0, y - tail, 0, y);
    trail.addColorStop(0, "transparent");
    trail.addColorStop(0.84, "#b6d9ed40");
    trail.addColorStop(1, "#c4dae067");

    paint.globalAlpha = 0.48 * fade;
    paint.strokeStyle = trail;
    paint.lineWidth = 1.15;
    paint.beginPath();
    paint.moveTo(x - 1.25, y - tail);
    paint.quadraticCurveTo(x + 1.2, y - tail * 0.44, x, y);
    paint.stroke();
    paint.fillStyle = "#b9cddd70";
    paint.fillRect(Math.round(x), Math.round(y), 1.4, 2.4);
  }
}

function drawPuddles(step) {
  nextRipple -= step;
  if (nextRipple <= 0) {
    const x = random(0.05, 0.95);
    ripples.push({
      x,
      y: random(portrait.matches ? 0.67 : 0.81, 0.97),
      age: 0,
      life: random(0.52, 0.94),
      size: random(5, 16),
      light: x > 0.28 && x < 0.66 ? "#f7c284" : "#9fb8ca",
    });
    nextRipple = random(0.16, 0.51);
  }

  const left = artLeft - pan.x * 8;
  const top = artTop - pan.y * 5;
  for (let i = ripples.length - 1; i >= 0; i--) {
    const ripple = ripples[i];
    ripple.age += step;
    if (ripple.age >= ripple.life) {
      ripples.splice(i, 1);
      continue;
    }
    const progress = ripple.age / ripple.life;
    const radius = 1 + ripple.size * progress;
    paint.globalAlpha = 0.27 * Math.sin(Math.PI * progress) * (1 - progress * 0.42);
    paint.strokeStyle = ripple.light;
    paint.lineWidth = 0.8;
    paint.beginPath();
    paint.ellipse(left + artWidth * ripple.x, top + artHeight * ripple.y, radius, radius * 0.20, 0, 0, Math.PI * 2);
    paint.stroke();
  }
}

function draw(now) {
  const step = lastFrame ? Math.min((now - lastFrame) / 1000, 0.04) : 1 / 60;
  lastFrame = now;
  const easing = 1 - Math.exp(-4.2 * step);
  pan.x += (pointer.x - pan.x) * easing;
  pan.y += (pointer.y - pan.y) * easing;
  art.style.setProperty("--pan-x", `${-pan.x * 8}px`);
  art.style.setProperty("--pan-y", `${-pan.y * 5}px`);

  paint.globalAlpha = 1;
  paint.clearRect(0, 0, width, height);
  drawPuddles(step);
  drawRain(step);
  drawGlass(step);
  frame = requestAnimationFrame(draw);
}

function restPointer() {
  pointer.x = 0;
  pointer.y = 0;
}

function syncMotion() {
  if (reducedMotion.matches || document.hidden) {
    cancelAnimationFrame(frame);
    frame = 0;
    lastFrame = 0;
    restPointer();
    pan.x = 0;
    pan.y = 0;
    art.style.setProperty("--pan-x", "0px");
    art.style.setProperty("--pan-y", "0px");
    paint.clearRect(0, 0, width, height);
  } else if (!frame) {
    frame = requestAnimationFrame(draw);
  }
}

scene.addEventListener("pointermove", (event) => {
  if (event.pointerType === "touch" || reducedMotion.matches) return;
  pointer.x = 2 * event.clientX / width - 1;
  pointer.y = 2 * event.clientY / height - 1;
}, { passive: true });
scene.addEventListener("pointerleave", restPointer);
window.addEventListener("blur", restPointer);
window.addEventListener("resize", resize, { passive: true });
portrait.addEventListener("change", resize);
reducedMotion.addEventListener("change", syncMotion);

sign.addEventListener("click", () => {
  flicker?.cancel();
  const shade = reducedMotion.matches
    ? [{ opacity: 0 }, { opacity: 0.18 }, { opacity: 0 }]
    : [
      { opacity: 0, offset: 0 },
      { opacity: 0.37, offset: 0.15 },
      { opacity: 0.05, offset: 0.29 },
      { opacity: 0.23, offset: 0.47 },
      { opacity: 0.06, offset: 0.67 },
      { opacity: 0, offset: 1 },
    ];
  flicker = signFace.animate(shade, { duration: 435 });
});

let sound;
let volume;
let wantsSound = false;
let interacted = false;

function createRainSound() {
  const Audio = window.AudioContext || window.webkitAudioContext;
  if (!Audio) return;

  sound = new Audio();
  const buffer = sound.createBuffer(2, Math.round(sound.sampleRate * 7), sound.sampleRate);
  for (let channel = 0; channel < buffer.numberOfChannels; channel++) {
    const samples = buffer.getChannelData(channel);
    const seam = 3072;
    let drift = 0;
    let soft = 0;
    for (let i = 0; i < samples.length; i++) {
      const noise = random(-1, 1);
      drift += (noise - drift) * 0.035;
      soft += (noise - soft) * 0.18;
      samples[i] = noise * 0.17 + soft * 0.57 + drift * 0.42;
    }
    for (let i = 0; i < seam; i++) {
      const mix = 0.5 - 0.5 * Math.cos(Math.PI * i / seam);
      samples[i] = samples[samples.length - seam + i] * (1 - mix) + samples[i] * mix;
    }
  }

  const source = sound.createBufferSource();
  source.buffer = buffer;
  source.loop = true;
  source.loopEnd = (buffer.length - 3072) / sound.sampleRate;
  const highpass = sound.createBiquadFilter();
  highpass.type = "highpass";
  highpass.frequency.value = 285;
  const lowpass = sound.createBiquadFilter();
  lowpass.type = "lowpass";
  lowpass.frequency.value = 3100;
  volume = sound.createGain();
  volume.gain.value = 0;
  source.connect(highpass).connect(lowpass).connect(volume).connect(sound.destination);
  source.start();
}

function syncSound() {
  if (wantsSound && !document.hidden) {
    if (!sound) createRainSound();
    if (sound?.state !== "running") sound?.resume().catch(() => {});
  }
  if (!volume) return;
  const now = sound.currentTime;
  volume.gain.cancelScheduledValues(now);
  volume.gain.setTargetAtTime(wantsSound && !document.hidden ? 0.095 : 0, now, 0.25);
}

scene.addEventListener("click", (event) => {
  if (!interacted) {
    interacted = true;
    wantsSound = true;
  } else if (!sign.contains(event.target)) {
    wantsSound = !wantsSound;
  }
  syncSound();
});
window.addEventListener("keydown", (event) => {
  if (event.key.toLowerCase() !== "m" || event.repeat || event.ctrlKey || event.metaKey || event.altKey) return;
  interacted = true;
  wantsSound = !wantsSound;
  syncSound();
});
document.addEventListener("visibilitychange", () => {
  syncMotion();
  syncSound();
});

resize();
