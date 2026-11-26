/**
 * AETHERIA — Fullscreen Interactive Particle Universe
 * Built purely with p5.js
 */

let glowBank;
let nebulaField;

let bgStars = [];
let particles = [];
let shockwaves = [];
let sparks = [];
let attractors = [];

let activePaletteIdx = 0;
let activePalette;
let targetPalette;
let paletteLerpPending = 0;

let flowModeIdx = 0;
let isPaused = false;
let simTime = 0;
let introDismissed = false;
let toastTimer = null;

const pointer = {
  x: 0,
  y: 0,
  targetX: 0,
  targetY: 0,
  vx: 0,
  vy: 0,
  speed: 0,
  active: false,
  pressed: false,
  holding: false,
  pressStart: 0,
  charge: 0,
  parallaxX: 0,
  parallaxY: 0
};

function setup() {
  const cnv = createCanvas(windowWidth, windowHeight);
  cnv.parent('canvas-root');
  pixelDensity(Math.min(window.devicePixelRatio || 1, 2));
  noiseDetail(3, 0.5);

  targetPalette = COSMIC_PALETTES[activePaletteIdx];
  activePalette = clonePalette(targetPalette);

  glowBank = new GlowSpriteBank();
  glowBank.rebuild(activePalette);

  nebulaField = new NebulaField();
  nebulaField.init(width, height, activePalette);

  initAttractors();
  initStarfield();
  initParticles();

  pointer.x = width * 0.5;
  pointer.y = height * 0.5;
  pointer.targetX = pointer.x;
  pointer.targetY = pointer.y;

  // Pre-warm particle universe so frame 1 already blooms with silky tapered trails
  prewarmUniverse(20);

  bindUIControls();

  // Gracefully fade out opening title after 4.2s
  setTimeout(dismissIntro, 4200);
}

function initAttractors() {
  attractors = [
    { x: width * 0.35, y: height * 0.42, baseAngle: 0.4, speed: 0.00042, rx: 0.24, ry: 0.2, spin: 1, strength: 1.05 },
    { x: width * 0.68, y: height * 0.56, baseAngle: 2.6, speed: -0.00034, rx: 0.26, ry: 0.22, spin: -1, strength: 0.95 },
    { x: width * 0.52, y: height * 0.5, baseAngle: 4.5, speed: 0.00028, rx: 0.16, ry: 0.14, spin: 1, strength: 0.8 }
  ];
}

function initStarfield() {
  bgStars = [];
  const area = width * height;
  const starCount = Math.max(110, Math.min(260, Math.floor(area / 6200)));
  for (let i = 0; i < starCount; i++) {
    bgStars.push(new BackgroundStar(width, height));
  }
}

function initParticles() {
  particles = [];
  const area = width * height;
  // Adaptive lush density: ~1350 on 1080p, scaled smoothly for smaller or 4K viewports
  const count = Math.max(900, Math.min(1850, Math.floor(area / 1280)));
  for (let i = 0; i < count; i++) {
    particles.push(new CosmicParticle(width, height, i));
  }
}

function prewarmUniverse(steps) {
  for (let s = 0; s < steps; s++) {
    simTime += 1.0;
    updateAttractors();

    const ctxState = {
      w: width,
      h: height,
      time: simTime,
      flowMode: flowModeIdx,
      attractors,
      pointer: { active: false, holding: false, charge: 0 },
      shockwaves: []
    };

    for (let i = 0; i < particles.length; i++) {
      particles[i].update(ctxState);
    }
  }
}

function updateAttractors() {
  for (const a of attractors) {
    const theta = simTime * a.speed + a.baseAngle;
    a.x = width * (0.5 + Math.cos(theta) * a.rx + Math.sin(theta * 1.7) * 0.05);
    a.y = height * (0.5 + Math.sin(theta * 0.9) * a.ry + Math.cos(theta * 1.3) * 0.05);
  }
}

function updatePointer() {
  const prevX = pointer.x;
  const prevY = pointer.y;
  pointer.x += (pointer.targetX - pointer.x) * 0.24;
  pointer.y += (pointer.targetY - pointer.y) * 0.24;
  pointer.vx = pointer.x - prevX;
  pointer.vy = pointer.y - prevY;
  pointer.speed = Math.hypot(pointer.vx, pointer.vy);

  // Smooth cursor parallax for deep-space depth
  const targetPx = pointer.active ? (pointer.x / Math.max(width, 1) - 0.5) * 2 : Math.sin(simTime * 0.002) * 0.2;
  const targetPy = pointer.active ? (pointer.y / Math.max(height, 1) - 0.5) * 2 : Math.cos(simTime * 0.0016) * 0.2;
  pointer.parallaxX += (targetPx - pointer.parallaxX) * 0.04;
  pointer.parallaxY += (targetPy - pointer.parallaxY) * 0.04;

  // Singularity hold charging
  if (pointer.pressed) {
    const elapsed = millis() - pointer.pressStart;
    if (elapsed > 175) {
      pointer.holding = true;
      pointer.charge = Math.min(1.0, (elapsed - 175) / 1450);
    }
  } else {
    pointer.holding = false;
    pointer.charge *= 0.85;
  }

  // Shed delicate micro-stardust embers when sweeping the cursor swiftly
  if (pointer.active && !pointer.holding && pointer.speed > 5.5 && !isPaused) {
    const spawnCount = Math.min(3, Math.floor(pointer.speed / 6.5));
    for (let i = 0; i < spawnCount; i++) {
      const col = activePalette.particles[Math.floor(random(activePalette.particles.length))];
      const spread = random(-0.45, 0.45);
      const svx = -pointer.vx * random(0.06, 0.16) + Math.cos(spread) * random(-0.8, 0.8);
      const svy = -pointer.vy * random(0.06, 0.16) + Math.sin(spread) * random(-0.8, 0.8);
      sparks.push(
        new StardustSpark(
          pointer.x + random(-8, 8),
          pointer.y + random(-8, 8),
          svx,
          svy,
          col,
          random(1.0, 2.2),
          random(24, 46),
          random(-0.025, 0.025)
        )
      );
    }
  }
}

function drawVectorParticleTrails(ctx) {
  // Batched tapered silk ribbons directly on main canvas:
  // 5 palette colors x 3 tapered opacity/width bands = 15 stroke calls total!
  // Zero offscreen ghosting, zero dark scratches, razor-sharp retina quality, instant palette shifts.
  const bands = [
    { start: 0, end: 5, alpha: 0.44, width: 1.6 },
    { start: 5, end: 11, alpha: 0.25, width: 1.15 },
    { start: 11, end: 16, alpha: 0.13, width: 0.8 },
    { start: 16, end: 21, alpha: 0.06, width: 0.55 }
  ];

  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  for (let cIdx = 0; cIdx < activePalette.particles.length; cIdx++) {
    const col = activePalette.particles[cIdx];
    const r = Math.round(col[0]);
    const g = Math.round(col[1]);
    const b = Math.round(col[2]);

    for (let bIdx = 0; bIdx < bands.length; bIdx++) {
      const band = bands[bIdx];
      ctx.beginPath();
      let hasPath = false;

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        if (p.colorIdx !== cIdx || p.trailCount <= band.start + 1) continue;
        if (p.getLifeAlpha() < 0.14) continue;

        const limit = Math.min(p.trailCount - 1, band.end);
        ctx.moveTo(p.trailX[band.start], p.trailY[band.start]);
        for (let k = band.start + 1; k <= limit; k++) {
          ctx.lineTo(p.trailX[k], p.trailY[k]);
        }
        hasPath = true;
      }

      if (hasPath) {
        ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${band.alpha})`;
        ctx.lineWidth = band.width;
        ctx.stroke();
      }
    }
  }

  // Extra luminous incandescent core ribbon for energized particles (near cursor / shockwaves)
  ctx.beginPath();
  let hasHot = false;
  for (let i = 0; i < particles.length; i++) {
    const p = particles[i];
    if (p.energy < 0.32 || p.trailCount < 3) continue;
    const limit = Math.min(p.trailCount - 1, 7);
    ctx.moveTo(p.trailX[0], p.trailY[0]);
    for (let k = 1; k <= limit; k++) {
      ctx.lineTo(p.trailX[k], p.trailY[k]);
    }
    hasHot = true;
  }
  if (hasHot) {
    ctx.strokeStyle = 'rgba(255, 248, 236, 0.38)';
    ctx.lineWidth = 1.65;
    ctx.stroke();
  }

  // Supernova & wake spark curved comet trails
  for (let i = 0; i < sparks.length; i++) {
    const sp = sparks[i];
    if (sp.trailCount < 2) continue;
    const heat = sp.life * sp.life;
    const r = Math.round(sp.color[0] + (255 - sp.color[0]) * heat * 0.55);
    const g = Math.round(sp.color[1] + (248 - sp.color[1]) * heat * 0.55);
    const b = Math.round(sp.color[2] + (234 - sp.color[2]) * heat * 0.55);

    ctx.beginPath();
    ctx.moveTo(sp.trailX[0], sp.trailY[0]);
    for (let k = 1; k < sp.trailCount; k++) {
      ctx.lineTo(sp.trailX[k], sp.trailY[k]);
    }
    ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${(sp.life * 0.68).toFixed(3)})`;
    ctx.lineWidth = sp.size * (0.45 + sp.life * 0.65);
    ctx.stroke();
  }

  ctx.restore();
}

function draw() {
  const ctx = drawingContext;

  // Smooth palette interpolation
  if (paletteLerpPending > 0) {
    blendPaletteInto(activePalette, targetPalette, 0.065);
    paletteLerpPending--;
    if (paletteLerpPending % 8 === 0 || paletteLerpPending === 0) {
      glowBank.rebuild(activePalette);
      nebulaField.rebuildSprites(activePalette);
    }
  }

  updatePointer();

  if (!isPaused) {
    simTime += 1.0;
    updateAttractors();

    // Update shockwaves
    for (let i = shockwaves.length - 1; i >= 0; i--) {
      if (!shockwaves[i].update()) {
        shockwaves.splice(i, 1);
      }
    }

    const ctxState = {
      w: width,
      h: height,
      time: simTime,
      flowMode: flowModeIdx,
      attractors,
      pointer,
      shockwaves
    };

    for (let i = 0; i < particles.length; i++) {
      particles[i].update(ctxState);
    }

    for (let i = sparks.length - 1; i >= 0; i--) {
      if (!sparks[i].update()) {
        sparks.splice(i, 1);
      }
    }
  }

  // --- LAYER 0: Deep Cosmic Void + Living Volumetric Nebula ---
  nebulaField.draw(ctx, simTime, pointer.parallaxX, pointer.parallaxY, activePalette.bgTop, activePalette.bgBottom);

  // --- LAYER 1: Distant Twinkling Starfield ---
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < bgStars.length; i++) {
    bgStars[i].draw(ctx, simTime, pointer.parallaxX, pointer.parallaxY);
  }
  ctx.restore();

  // --- LAYER 2: Razor-Sharp Tapered Luminous Light Trails ---
  drawVectorParticleTrails(ctx);

  // --- LAYER 3: Foreground Glowing Star Heads & Optical Diffraction Flares ---
  drawGlowingStars(ctx);

  // --- LAYER 4: Ephemeral Starlight Constellations near Cursor ---
  if (pointer.active) {
    drawCursorConstellations(ctx);
  }

  // --- LAYER 5: Supernova Shockwaves & Sparkling Newborn Embers ---
  for (let i = 0; i < shockwaves.length; i++) {
    shockwaves[i].draw(ctx, simTime);
  }
  drawSparkHeads(ctx);

  // --- LAYER 6: Celestial Cursor Aura & Gravitational Singularity ---
  if (pointer.active) {
    drawCursorPhenomenon(ctx);
  }
}

function drawGlowingStars(ctx) {
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';

  for (let i = 0; i < particles.length; i++) {
    const p = particles[i];
    const lifeAlpha = p.getLifeAlpha();
    if (lifeAlpha <= 0.02) continue;

    const e = p.energy;
    const isFlare = p.tier === 2 || (p.tier === 1 && e > 0.65);
    const sprite = isFlare
      ? glowBank.flareSprites[p.colorIdx]
      : glowBank.softSprites[p.colorIdx];
    if (!sprite) continue;

    const pulse = 0.88 + 0.12 * Math.sin(simTime * 0.045 + p.seed);
    const radius = (p.baseSize * (isFlare ? 6.2 : 4.2) + e * 9.5) * pulse;
    ctx.globalAlpha = Math.min(1.0, (0.38 + p.depth * 0.42 + e * 0.45) * lifeAlpha);
    ctx.drawImage(sprite.canvas, p.x - radius, p.y - radius, radius * 2, radius * 2);
  }
  ctx.restore();
}

function drawSparkHeads(ctx) {
  if (sparks.length === 0 || !glowBank.whiteCore) return;
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < sparks.length; i++) {
    const sp = sparks[i];
    const flicker = 0.72 + 0.28 * Math.sin(simTime * 0.25 + sp.twinkleOffset);
    const r = sp.size * (2.2 + sp.life * 2.4) * flicker;
    ctx.globalAlpha = Math.min(0.85, sp.life * 0.88);
    ctx.drawImage(glowBank.whiteCore.canvas, sp.x - r, sp.y - r, r * 2, r * 2);
  }
  ctx.restore();
}

function drawCursorConstellations(ctx) {
  // Collect closest stars near cursor (bounded to 24 for ultra-fast O(k^2) gossamer star-web)
  const radius = pointer.holding ? 185 + pointer.charge * 60 : 145;
  const rSq = radius * radius;
  const nearby = [];

  for (let i = 0; i < particles.length; i++) {
    const p = particles[i];
    const dx = p.x - pointer.x;
    const dy = p.y - pointer.y;
    const dSq = dx * dx + dy * dy;
    if (dSq < rSq && p.getLifeAlpha() > 0.25) {
      nearby.push({ p, dSq });
      if (nearby.length >= 26) break;
    }
  }

  if (nearby.length < 2) return;

  const [cr, cg, cb] = activePalette.burstRingA.map(Math.round);
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.lineWidth = 0.75;

  const linkDistSq = 92 * 92;
  for (let i = 0; i < nearby.length; i++) {
    const a = nearby[i].p;
    for (let j = i + 1; j < nearby.length; j++) {
      const b = nearby[j].p;
      const dx = a.x - b.x;
      const dy = a.y - b.y;
      const dSq = dx * dx + dy * dy;
      if (dSq < linkDistSq) {
        const proximity = 1 - Math.sqrt(dSq) / 92;
        const alpha = proximity * proximity * (pointer.holding ? 0.24 : 0.16);
        ctx.strokeStyle = `rgba(${cr}, ${cg}, ${cb}, ${alpha.toFixed(3)})`;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }
    }
  }
  ctx.restore();
}

function drawCursorPhenomenon(ctx) {
  const [sr, sg, sb] = activePalette.singularity.map(Math.round);
  const [ar, ag, ab] = activePalette.burstRingA.map(Math.round);

  if (pointer.holding && pointer.charge > 0.04) {
    // Relativistic Singularity / Accretion Disk
    const c = pointer.charge;
    const coreR = 11 + c * 15;
    const haloR = 54 + c * 88;

    ctx.save();
    // Outer photon aura
    ctx.globalCompositeOperation = 'lighter';
    const aura = ctx.createRadialGradient(pointer.x, pointer.y, coreR * 0.6, pointer.x, pointer.y, haloR);
    aura.addColorStop(0.0, `rgba(255, 246, 232, ${(0.22 + c * 0.42).toFixed(3)})`);
    aura.addColorStop(0.28, `rgba(${sr}, ${sg}, ${sb}, ${(0.24 + c * 0.34).toFixed(3)})`);
    aura.addColorStop(0.65, `rgba(${ar}, ${ag}, ${ab}, ${(0.08 + c * 0.14).toFixed(3)})`);
    aura.addColorStop(1.0, `rgba(${ar}, ${ag}, ${ab}, 0)`);
    ctx.fillStyle = aura;
    ctx.beginPath();
    ctx.arc(pointer.x, pointer.y, haloR, 0, TWO_PI);
    ctx.fill();

    // Spinning accretion arcs
    ctx.translate(pointer.x, pointer.y);
    for (let k = 0; k < 3; k++) {
      ctx.save();
      ctx.rotate(simTime * (0.045 + k * 0.022) * (k % 2 === 0 ? 1 : -1) + k * 2.1);
      ctx.scale(1, 0.74 + k * 0.11);
      ctx.strokeStyle = `rgba(255, 238, 212, ${(0.2 + c * 0.5).toFixed(3)})`;
      ctx.lineWidth = 1.1 + c * 1.1;
      ctx.beginPath();
      ctx.arc(0, 0, coreR + 8 + k * 9 + c * 14, 0, PI * (0.9 + c * 0.65));
      ctx.stroke();
      ctx.restore();
    }

    // Dark event horizon center
    ctx.globalCompositeOperation = 'source-over';
    const voidGrad = ctx.createRadialGradient(0, 0, 0, 0, 0, coreR * 1.25);
    voidGrad.addColorStop(0.0, 'rgba(2, 3, 10, 0.96)');
    voidGrad.addColorStop(0.74, 'rgba(5, 6, 18, 0.88)');
    voidGrad.addColorStop(1.0, 'rgba(5, 6, 18, 0)');
    ctx.fillStyle = voidGrad;
    ctx.beginPath();
    ctx.arc(0, 0, coreR * 1.25, 0, TWO_PI);
    ctx.fill();

    // Crisp luminous photon ring on the horizon rim
    ctx.globalCompositeOperation = 'lighter';
    ctx.strokeStyle = `rgba(255, 244, 224, ${(0.45 + c * 0.5).toFixed(3)})`;
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.arc(0, 0, coreR * 0.94, 0, TWO_PI);
    ctx.stroke();
    ctx.restore();
  } else {
    // Whisper-subtle celestial cursor aura
    const breath = 1 + Math.sin(simTime * 0.05) * 0.1;
    const radius = (28 + Math.min(pointer.speed * 1.8, 34)) * breath;

    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    const aura = ctx.createRadialGradient(pointer.x, pointer.y, 0, pointer.x, pointer.y, radius);
    aura.addColorStop(0.0, 'rgba(255, 252, 245, 0.22)');
    aura.addColorStop(0.32, `rgba(${ar}, ${ag}, ${ab}, 0.11)`);
    aura.addColorStop(1.0, `rgba(${ar}, ${ag}, ${ab}, 0)`);
    ctx.fillStyle = aura;
    ctx.beginPath();
    ctx.arc(pointer.x, pointer.y, radius, 0, TWO_PI);
    ctx.fill();
    ctx.restore();
  }
}

function triggerSupernova(x, y, power = 1.0) {
  dismissIntro();

  // Multi-layered plasma shockwave + nebula bloom
  shockwaves.push(new Shockwave(x, y, power, activePalette));
  nebulaField.addFlash(x, y, activePalette.burstRingA, power);

  // Newborn incandescent stardust burst (spawned on an expanding delicate halo to prevent white clipping)
  const sparkCount = Math.round(38 + power * 44);
  const swirlBias = random() < 0.5 ? 1 : -1;
  for (let i = 0; i < sparkCount; i++) {
    const angle = (i / sparkCount) * TWO_PI + random(-0.2, 0.2);
    const speed = random(2.4, 7.2 + power * 4.4) * (random() < 0.28 ? 1.4 : 1.0);
    const color = activePalette.particles[i % activePalette.particles.length];
    const size = random(0.85, 2.0 + power * 0.65);
    const life = random(38, 84 + power * 34);
    const curl = swirlBias * random(0.01, 0.032);
    const spawnRad = random(10, 26);

    sparks.push(
      new StardustSpark(
        x + Math.cos(angle) * spawnRad,
        y + Math.sin(angle) * spawnRad,
        Math.cos(angle) * speed,
        Math.sin(angle) * speed,
        color,
        size,
        life,
        curl
      )
    );
  }

  // Immediate radial + swirl kick on nearby particles without evacuating the screen center
  const blastR = 135 + power * 115;
  const blastRSq = blastR * blastR;
  for (let i = 0; i < particles.length; i++) {
    const p = particles[i];
    const dx = p.x - x;
    const dy = p.y - y;
    const dSq = dx * dx + dy * dy;
    if (dSq < blastRSq && dSq > 0.01) {
      const dist = Math.sqrt(dSq);
      const falloff = 1 - dist / blastR;
      const nx = dx / dist;
      const ny = dy / dist;
      const impulse = (2.1 + power * 3.4) * falloff * falloff;
      p.vx += nx * impulse - ny * impulse * 0.42 * swirlBias;
      p.vy += ny * impulse + nx * impulse * 0.42 * swirlBias;
      p.energy = Math.min(1.0, p.energy + falloff * (0.55 + power * 0.35));
    }
  }
}

/* ---------- Pointer, Touch & Keyboard Events ---------- */

function isEventOnHUD(evt) {
  return evt && evt.target && typeof evt.target.closest === 'function' && Boolean(evt.target.closest('.hud-interactive'));
}

function mouseMoved(evt) {
  if (isEventOnHUD(evt)) return;
  pointer.active = true;
  pointer.targetX = mouseX;
  pointer.targetY = mouseY;
}

function mouseDragged(evt) {
  if (isEventOnHUD(evt)) return;
  pointer.active = true;
  pointer.targetX = mouseX;
  pointer.targetY = mouseY;
}

function mousePressed(evt) {
  if (isEventOnHUD(evt)) return;
  if (mouseButton !== LEFT) return;
  dismissIntro();
  pointer.active = true;
  pointer.targetX = mouseX;
  pointer.targetY = mouseY;
  pointer.x = mouseX;
  pointer.y = mouseY;
  pointer.pressed = true;
  pointer.pressStart = millis();
  pointer.charge = 0;
}

function mouseReleased(evt) {
  if (!pointer.pressed) return;
  const wasHolding = pointer.holding;
  const charge = pointer.charge;
  pointer.pressed = false;
  pointer.holding = false;

  if (isEventOnHUD(evt)) return;

  if (wasHolding) {
    // Singularity detonation scaled by accumulated energy
    triggerSupernova(pointer.x, pointer.y, 1.1 + charge * 1.45);
  } else {
    // Crisp poetic supernova pulse on quick click
    triggerSupernova(mouseX, mouseY, 0.92);
  }
}

function touchStarted(evt) {
  if (isEventOnHUD(evt)) return true;
  if (touches.length > 0) {
    dismissIntro();
    pointer.active = true;
    pointer.x = touches[0].x;
    pointer.y = touches[0].y;
    pointer.targetX = touches[0].x;
    pointer.targetY = touches[0].y;
    pointer.pressed = true;
    pointer.pressStart = millis();
    pointer.charge = 0;
  }
  return false;
}

function touchMoved(evt) {
  if (isEventOnHUD(evt)) return true;
  if (touches.length > 0) {
    pointer.active = true;
    pointer.targetX = touches[0].x;
    pointer.targetY = touches[0].y;
  }
  return false;
}

function touchEnded(evt) {
  if (isEventOnHUD(evt)) return true;
  if (pointer.pressed) {
    const wasHolding = pointer.holding;
    const charge = pointer.charge;
    pointer.pressed = false;
    pointer.holding = false;
    triggerSupernova(pointer.x, pointer.y, wasHolding ? 1.1 + charge * 1.45 : 0.92);
  }
  return false;
}

function handleGlobalShortcut(rawKey, evt) {
  if (evt && (evt.ctrlKey || evt.metaKey || evt.altKey)) return;
  if (rawKey >= '1' && rawKey <= '4') {
    setPalette(parseInt(rawKey, 10) - 1);
  } else if (rawKey === 'c' || rawKey === 'C') {
    setPalette((activePaletteIdx + 1) % COSMIC_PALETTES.length);
  } else if (rawKey === 'm' || rawKey === 'M') {
    cycleFlowMode();
  } else if (rawKey === ' ') {
    if (evt) evt.preventDefault();
    togglePause();
  } else if (rawKey === 's' || rawKey === 'S') {
    captureArtwork();
  } else if (rawKey === 'h' || rawKey === 'H') {
    toggleHelp();
  }
}

function windowResized() {
  resizeCanvas(windowWidth, windowHeight);

  nebulaField.init(width, height, activePalette);
  initAttractors();
  initStarfield();

  // Gently adjust particle count to match new viewport area
  const targetCount = Math.max(900, Math.min(1850, Math.floor((width * height) / 1280)));
  if (particles.length < targetCount) {
    for (let i = particles.length; i < targetCount; i++) {
      particles.push(new CosmicParticle(width, height, i));
    }
  } else if (particles.length > targetCount) {
    particles.length = targetCount;
  }
}

/* ---------- Minimal HUD Synchronization ---------- */

function dismissIntro() {
  if (introDismissed) return;
  introDismissed = true;
  const el = document.getElementById('intro-overlay');
  if (el) el.classList.add('is-hidden');
}

function showToast(text) {
  const toast = document.getElementById('mode-toast');
  if (!toast) return;
  toast.textContent = text;
  toast.classList.add('is-visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('is-visible'), 2200);
}

function setPalette(idx) {
  dismissIntro();
  activePaletteIdx = idx;
  targetPalette = COSMIC_PALETTES[activePaletteIdx];
  paletteLerpPending = 55;

  document.querySelectorAll('.palette-dot').forEach((dot, i) => {
    dot.classList.toggle('active', i === activePaletteIdx);
  });

  showToast(`${targetPalette.name} · ${targetPalette.subtitle}`);
}

function cycleFlowMode() {
  dismissIntro();
  flowModeIdx = (flowModeIdx + 1) % FLOW_MODES.length;
  const mode = FLOW_MODES[flowModeIdx];
  const label = document.getElementById('btn-mode-label');
  if (label) label.textContent = mode.name;
  showToast(`${mode.name} · ${mode.subtitle}`);
}

function togglePause() {
  dismissIntro();
  isPaused = !isPaused;
  const btn = document.getElementById('btn-pause');
  if (btn) {
    btn.classList.toggle('is-active', isPaused);
    btn.innerHTML = isPaused
      ? '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><polygon points="7,5 19,12 7,19"></polygon></svg>'
      : '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"></rect><rect x="14" y="5" width="4" height="14" rx="1"></rect></svg>';
  }
  showToast(isPaused ? '时光凝固 · PAUSED' : '星河续流 · RESUMED');
}

function captureArtwork() {
  dismissIntro();
  const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  saveCanvas(`AETHERIA-${COSMIC_PALETTES[activePaletteIdx].id}-${stamp}`, 'png');
  showToast('已捕获宇宙瞬间 · SAVED PNG');
}

function toggleHelp() {
  dismissIntro();
  const card = document.getElementById('help-card');
  const btn = document.getElementById('btn-help');
  if (!card) return;
  const open = card.classList.toggle('is-open');
  card.setAttribute('aria-hidden', String(!open));
  if (btn) btn.classList.toggle('is-active', open);
}

function bindUIControls() {
  document.querySelectorAll('.palette-dot').forEach(dot => {
    dot.addEventListener('click', e => {
      e.stopPropagation();
      setPalette(parseInt(dot.dataset.palette, 10));
    });
  });

  const btnMode = document.getElementById('btn-mode');
  if (btnMode) {
    btnMode.addEventListener('click', e => {
      e.stopPropagation();
      cycleFlowMode();
    });
  }

  const btnPause = document.getElementById('btn-pause');
  if (btnPause) {
    btnPause.addEventListener('click', e => {
      e.stopPropagation();
      togglePause();
    });
  }

  const btnCapture = document.getElementById('btn-capture');
  if (btnCapture) {
    btnCapture.addEventListener('click', e => {
      e.stopPropagation();
      captureArtwork();
    });
  }

  const btnHelp = document.getElementById('btn-help');
  if (btnHelp) {
    btnHelp.addEventListener('click', e => {
      e.stopPropagation();
      toggleHelp();
    });
  }

  // Leave canvas cleanly when mouse leaves viewport
  document.addEventListener('mouseleave', () => {
    pointer.active = false;
    pointer.pressed = false;
    pointer.holding = false;
  });

  // Reliable keyboard shortcuts regardless of canvas/button focus
  window.addEventListener('keydown', e => {
    handleGlobalShortcut(e.key, e);
  });
}
