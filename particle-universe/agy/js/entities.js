/**
 * Core visual & physics entities for AETHERIA using p5.js.
 * - GlowSpriteBank: pre-rendered optical star & flare textures for crisp 60fps glow
 * - NebulaField: living multi-layered volumetric cosmic gas clouds
 * - BackgroundStar: distant twinkling deep-field stars with cursor parallax
 * - CosmicParticle: flow-field & gravitational luminous stars with smooth lifecycles
 * - Shockwave: chromatic expanding plasma rings from supernova clicks
 * - StardustSpark: newborn high-luminance embers with curved trails
 */

class GlowSpriteBank {
  constructor() {
    this.softSprites = [];
    this.flareSprites = [];
    this.whiteCore = null;
    this.size = 64;
    this.flareSize = 96;
  }

  rebuild(palette) {
    this.softSprites.forEach(g => g.remove());
    this.flareSprites.forEach(g => g.remove());
    if (this.whiteCore) this.whiteCore.remove();

    this.softSprites = palette.particles.map(rgb => this._createSoftGlow(rgb));
    this.flareSprites = palette.particles.map(rgb => this._createFlareGlow(rgb));
    this.whiteCore = this._createSoftGlow([255, 250, 240]);
  }

  _createSoftGlow(rgb) {
    const s = this.size;
    const g = createGraphics(s, s);
    g.pixelDensity(1);
    const ctx = g.drawingContext;
    const half = s * 0.5;
    const [r, gr, b] = rgb.map(Math.round);

    const grad = ctx.createRadialGradient(half, half, 0, half, half, half);
    grad.addColorStop(0.0, 'rgba(255, 255, 255, 1.0)');
    grad.addColorStop(0.14, `rgba(${Math.min(255, r + 60)}, ${Math.min(255, gr + 60)}, ${Math.min(255, b + 60)}, 0.92)`);
    grad.addColorStop(0.36, `rgba(${r}, ${gr}, ${b}, 0.42)`);
    grad.addColorStop(0.68, `rgba(${r}, ${gr}, ${b}, 0.10)`);
    grad.addColorStop(1.0, `rgba(${r}, ${gr}, ${b}, 0.0)`);

    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, s, s);
    return g;
  }

  _createFlareGlow(rgb) {
    const s = this.flareSize;
    const g = createGraphics(s, s);
    g.pixelDensity(1);
    const ctx = g.drawingContext;
    const half = s * 0.5;
    const [r, gr, b] = rgb.map(Math.round);

    // Outer optical halo
    const grad = ctx.createRadialGradient(half, half, 0, half, half, half);
    grad.addColorStop(0.0, 'rgba(255, 255, 255, 1.0)');
    grad.addColorStop(0.12, `rgba(${Math.min(255, r + 80)}, ${Math.min(255, gr + 80)}, ${Math.min(255, b + 80)}, 0.9)`);
    grad.addColorStop(0.32, `rgba(${r}, ${gr}, ${b}, 0.35)`);
    grad.addColorStop(0.7, `rgba(${r}, ${gr}, ${b}, 0.06)`);
    grad.addColorStop(1.0, `rgba(${r}, ${gr}, ${b}, 0.0)`);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, s, s);

    // Subtle 4-point astronomical diffraction spikes
    ctx.save();
    ctx.translate(half, half);
    ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 2; i++) {
      ctx.save();
      ctx.rotate(i * HALF_PI);
      const spike = ctx.createLinearGradient(-half * 0.92, 0, half * 0.92, 0);
      spike.addColorStop(0.0, `rgba(${r}, ${gr}, ${b}, 0.0)`);
      spike.addColorStop(0.38, `rgba(${r}, ${gr}, ${b}, 0.18)`);
      spike.addColorStop(0.5, 'rgba(255, 255, 255, 0.72)');
      spike.addColorStop(0.62, `rgba(${r}, ${gr}, ${b}, 0.18)`);
      spike.addColorStop(1.0, `rgba(${r}, ${gr}, ${b}, 0.0)`);
      ctx.fillStyle = spike;
      ctx.beginPath();
      ctx.ellipse(0, 0, half * 0.92, 1.35, 0, 0, TWO_PI);
      ctx.fill();
      ctx.restore();
    }
    ctx.restore();

    return g;
  }
}

class NebulaField {
  constructor() {
    this.clouds = [];
    this.sprites = [];
    this.flashBlooms = [];
  }

  init(w, h, palette) {
    this.clouds = [];
    const count = 11;
    const minDim = Math.min(w, h);

    for (let i = 0; i < count; i++) {
      // Distribute organically around the frame with a richer galactic core band
      const angle = (i / count) * TWO_PI + random(-0.4, 0.4);
      const distFactor = i < 4 ? random(0.04, 0.22) : random(0.22, 0.46);
      this.clouds.push({
        baseX: w * 0.5 + Math.cos(angle) * w * distFactor,
        baseY: h * 0.5 + Math.sin(angle) * h * distFactor * 0.8,
        radius: minDim * random(0.32, 0.62),
        colorIdx: i % 4,
        phase: random(TWO_PI),
        speed: random(0.00025, 0.00055),
        driftAmp: minDim * random(0.03, 0.08),
        aspectX: random(0.95, 1.65),
        aspectY: random(0.65, 1.15),
        rot: random(TWO_PI),
        rotSpeed: random(-0.00035, 0.00035),
        alpha: random(0.16, 0.28),
        depth: random(0.3, 0.85)
      });
    }
    this.rebuildSprites(palette);
  }

  rebuildSprites(palette) {
    this.sprites.forEach(s => s.remove());
    this.sprites = palette.nebula.map(rgb => this._createCloudSprite(rgb));
  }

  _createCloudSprite(rgb) {
    const s = 256;
    const g = createGraphics(s, s);
    g.pixelDensity(1);
    const ctx = g.drawingContext;
    const [r, gr, b] = rgb.map(Math.round);

    // Layer several slightly offset soft gradients to create organic billowing gas rather than a plain circle
    const lobes = [
      { ox: 0.0, oy: 0.0, rad: 0.48, a: 0.58 },
      { ox: -0.14, oy: -0.08, rad: 0.36, a: 0.44 },
      { ox: 0.16, oy: 0.09, rad: 0.34, a: 0.42 },
      { ox: 0.05, oy: -0.15, rad: 0.30, a: 0.34 },
      { ox: -0.09, oy: 0.15, rad: 0.28, a: 0.32 }
    ];

    for (const lobe of lobes) {
      const cx = s * (0.5 + lobe.ox);
      const cy = s * (0.5 + lobe.oy);
      const rad = s * lobe.rad;
      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, rad);
      grad.addColorStop(0.0, `rgba(${Math.min(255, r + 35)}, ${Math.min(255, gr + 35)}, ${Math.min(255, b + 35)}, ${lobe.a})`);
      grad.addColorStop(0.42, `rgba(${r}, ${gr}, ${b}, ${lobe.a * 0.46})`);
      grad.addColorStop(0.76, `rgba(${r}, ${gr}, ${b}, ${lobe.a * 0.12})`);
      grad.addColorStop(1.0, `rgba(${r}, ${gr}, ${b}, 0.0)`);
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, s, s);
    }

    return g;
  }

  addFlash(x, y, rgb, power = 1.0) {
    this.flashBlooms.push({
      x,
      y,
      rgb: [...rgb],
      radius: 40,
      maxRadius: Math.min(width, height) * (0.28 + power * 0.18),
      life: 1.0,
      decay: 0.018 / Math.max(0.7, power)
    });
  }

  draw(ctx, time, parallaxX, parallaxY, bgTop, bgBottom) {
    // Rich cosmic void gradient
    const bgGrad = ctx.createRadialGradient(
      width * 0.5 + parallaxX * 18,
      height * 0.48 + parallaxY * 18,
      Math.min(width, height) * 0.04,
      width * 0.5,
      height * 0.5,
      Math.max(width, height) * 0.85
    );
    bgGrad.addColorStop(
      0,
      `rgb(${Math.round(bgBottom[0] * 1.15)}, ${Math.round(bgBottom[1] * 1.15)}, ${Math.round(bgBottom[2] * 1.25)})`
    );
    bgGrad.addColorStop(
      0.65,
      `rgb(${Math.round(bgTop[0] * 1.1)}, ${Math.round(bgTop[1] * 1.1)}, ${Math.round(bgTop[2] * 1.15)})`
    );
    bgGrad.addColorStop(
      1,
      `rgb(${Math.round(bgTop[0] * 0.72)}, ${Math.round(bgTop[1] * 0.72)}, ${Math.round(bgTop[2] * 0.82)})`
    );

    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = 1;
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, width, height);

    // Volumetric drifting nebula clouds
    ctx.save();
    ctx.globalCompositeOperation = 'screen';
    for (const c of this.clouds) {
      const sprite = this.sprites[c.colorIdx];
      if (!sprite) continue;
      const t = time * c.speed + c.phase;
      const breathe = 1 + Math.sin(t * 1.7) * 0.08;
      const x = c.baseX + Math.cos(t) * c.driftAmp + parallaxX * 42 * c.depth;
      const y = c.baseY + Math.sin(t * 0.83) * c.driftAmp + parallaxY * 42 * c.depth;
      const drawW = c.radius * 2 * c.aspectX * breathe;
      const drawH = c.radius * 2 * c.aspectY * breathe;

      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(c.rot + time * c.rotSpeed);
      ctx.globalAlpha = c.alpha * (0.88 + 0.12 * Math.sin(t * 2.1));
      ctx.drawImage(sprite.canvas, -drawW * 0.5, -drawH * 0.5, drawW, drawH);
      ctx.restore();
    }

    // Transient localized nebula blooms from supernovas
    ctx.globalCompositeOperation = 'lighter';
    for (let i = this.flashBlooms.length - 1; i >= 0; i--) {
      const f = this.flashBlooms[i];
      f.radius += (f.maxRadius - f.radius) * 0.09;
      f.life -= f.decay;
      if (f.life <= 0) {
        this.flashBlooms.splice(i, 1);
        continue;
      }
      const alpha = f.life * f.life * 0.34;
      const [r, g, b] = f.rgb.map(Math.round);
      const grad = ctx.createRadialGradient(f.x, f.y, 0, f.x, f.y, f.radius);
      grad.addColorStop(0.0, `rgba(255, 250, 240, ${alpha * 0.95})`);
      grad.addColorStop(0.32, `rgba(${r}, ${g}, ${b}, ${alpha * 0.55})`);
      grad.addColorStop(1.0, `rgba(${r}, ${g}, ${b}, 0)`);
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(f.x, f.y, f.radius, 0, TWO_PI);
      ctx.fill();
    }
    ctx.restore();
  }
}

class BackgroundStar {
  constructor(w, h) {
    this.x = random(w);
    this.y = random(h);
    this.depth = random(0.15, 0.95);
    this.size = random() < 0.86 ? random(0.55, 1.35) : random(1.4, 2.25);
    this.baseAlpha = random(0.18, 0.72);
    this.twinklePhase = random(TWO_PI);
    this.twinkleSpeed = random(0.015, 0.055);
    // Natural blackbody star tints: blue-white, ivory, soft warm gold
    const tintRoll = random();
    if (tintRoll < 0.42) {
      this.color = [212, 232, 255];
    } else if (tintRoll < 0.78) {
      this.color = [245, 246, 255];
    } else {
      this.color = [255, 224, 186];
    }
  }

  draw(ctx, time, parallaxX, parallaxY) {
    const px = (this.x + parallaxX * 26 * this.depth + width) % width;
    const py = (this.y + parallaxY * 26 * this.depth + height) % height;
    const twinkle = 0.62 + 0.38 * Math.sin(time * this.twinkleSpeed + this.twinklePhase);
    const alpha = this.baseAlpha * twinkle;

    ctx.fillStyle = `rgba(${this.color[0]}, ${this.color[1]}, ${this.color[2]}, ${alpha.toFixed(3)})`;
    ctx.beginPath();
    ctx.arc(px, py, this.size, 0, TWO_PI);
    ctx.fill();
  }
}

class CosmicParticle {
  constructor(w, h, index) {
    this.index = index;
    this.trailLen = 22;
    this.trailX = new Float32Array(this.trailLen);
    this.trailY = new Float32Array(this.trailLen);
    this.trailCount = 0;
    this.reset(w, h, true);
  }

  reset(w, h, initial = false) {
    // Bias initial placement into graceful cosmic bands and galactic cluster density
    const placementRoll = random();
    if (placementRoll < 0.7) {
      const angle = random(TWO_PI);
      const radial = Math.pow(random(), 0.72) * Math.max(w, h) * 0.48;
      this.x = w * 0.5 + Math.cos(angle) * radial * 1.12;
      this.y = h * 0.5 + Math.sin(angle) * radial * 0.86;
    } else {
      this.x = random(w);
      this.y = random(h);
    }

    this.px = this.x;
    this.py = this.y;
    this.clearTrail();

    // Gentle initial orbital drift
    const dx = this.x - w * 0.5;
    const dy = this.y - h * 0.5;
    const dist = Math.hypot(dx, dy) + 1;
    this.vx = (-dy / dist) * random(0.4, 1.3);
    this.vy = (dx / dist) * random(0.4, 1.3);

    this.depth = random(0.38, 1.0);
    // Power-law stellar magnitude distribution: lots of fine stardust, occasional radiant hero stars
    const sizeRoll = random();
    if (sizeRoll < 0.78) {
      this.tier = 0; // delicate cosmic dust
      this.baseSize = random(0.9, 1.85) * this.depth;
    } else if (sizeRoll < 0.955) {
      this.tier = 1; // luminous star
      this.baseSize = random(2.0, 3.2) * this.depth;
    } else {
      this.tier = 2; // radiant hero star with diffraction flare
      this.baseSize = random(3.3, 4.9) * this.depth;
    }

    this.colorIdx = Math.floor(random(5));
    this.maxSpeed = (1.8 + this.depth * 2.2) * (this.tier === 2 ? 0.85 : 1.0);
    this.energy = random(0.05, 0.25);
    this.age = initial ? random(0, 260) : 0;
    this.maxAge = random(380, 820);
    this.seed = random(1000);
    this.orbitSign = random() < 0.82 ? 1 : -1;
  }

  clearTrail() {
    this.trailX[0] = this.x;
    this.trailY[0] = this.y;
    this.trailCount = 1;
  }

  pushTrail() {
    const maxIdx = Math.min(this.trailCount, this.trailLen - 1);
    for (let i = maxIdx; i > 0; i--) {
      this.trailX[i] = this.trailX[i - 1];
      this.trailY[i] = this.trailY[i - 1];
    }
    this.trailX[0] = this.x;
    this.trailY[0] = this.y;
    if (this.trailCount < this.trailLen) this.trailCount++;
  }

  update(ctxState) {
    const {
      w, h, time, flowMode, attractors,
      pointer, shockwaves
    } = ctxState;

    this.px = this.x;
    this.py = this.y;
    this.age++;

    if (this.age >= this.maxAge) {
      this.reset(w, h, false);
      return;
    }

    let ax = 0;
    let ay = 0;
    const cx = w * 0.5;
    const cy = h * 0.5;
    const dxC = this.x - cx;
    const dyC = this.y - cy;
    const distC = Math.hypot(dxC, dyC) + 0.001;

    // 1. Primary Cosmic Flow Field (3 artistic modes)
    if (flowMode === 0) {
      // Cosmic Drift: curl-like multi-scale Perlin flow + wandering gravitational rivers
      const nScale = 0.00165;
      const n1 = noise(this.x * nScale, this.y * nScale, time * 0.00022);
      const n2 = noise(this.x * nScale * 2.4 + 41.3, this.y * nScale * 2.4 + 17.8, time * 0.00038);
      const flowAngle = n1 * TWO_PI * 2.35 + (n2 - 0.5) * 1.45;
      const flowStrength = 0.082 * this.depth;
      ax += Math.cos(flowAngle) * flowStrength;
      ay += Math.sin(flowAngle) * flowStrength;

      // Subtle galactic swirl around drifting harmonic attractors
      for (let i = 0; i < attractors.length; i++) {
        const att = attractors[i];
        const adx = att.x - this.x;
        const ady = att.y - this.y;
        const dSq = adx * adx + ady * ady + 18000;
        const invD = 1 / Math.sqrt(dSq);
        const pull = (att.strength * 24) / dSq;
        // Mix inward gravity with tangential orbital swirl
        ax += (adx * invD * 0.42 - ady * invD * att.spin * 0.85) * pull * 95;
        ay += (ady * invD * 0.42 + adx * invD * att.spin * 0.85) * pull * 95;
      }
    } else if (flowMode === 1) {
      // Spiral Nebula: balanced logarithmic galactic arms without edge pile-up
      const baseAngle = Math.atan2(dyC, dxC);
      const minDim = Math.min(w, h);
      const nxC = dxC / distC;
      const nyC = dyC / distC;
      const txC = -nyC;
      const tyC = nxC;

      // 2-arm galactic density wave modulation
      const armWave = Math.sin(baseAngle * 2 - distC * 0.014 + time * 0.0022);
      const preferredR = minDim * (0.045 + Math.pow((this.seed % 100) / 100, 0.78) * 0.44);
      const targetSpeed = (1.3 + (1 - Math.min(1, distC / (minDim * 0.55))) * 1.65) * this.depth;

      // Smoothly steer toward orbital tangential flow + radial home band (cancels centrifugal drift)
      const desiredVx = txC * targetSpeed * (1 + armWave * 0.24) - nxC * (distC - preferredR) * 0.016;
      const desiredVy = tyC * targetSpeed * (1 + armWave * 0.24) - nyC * (distC - preferredR) * 0.016;
      ax += (desiredVx - this.vx) * 0.045;
      ay += (desiredVy - this.vy) * 0.045;

      // Delicate organic turbulence so spiral arms feel like drifting nebular gas
      const nAngle = (noise(this.x * 0.0022, this.y * 0.0022, time * 0.0003) - 0.5) * TWO_PI;
      ax += Math.cos(nAngle) * 0.028 * this.depth;
      ay += Math.sin(nAngle) * 0.028 * this.depth;
    } else {
      // Harmonic Orbit: standing wave interference & luminous orbital ribbons
      const nx = (this.x - cx) / Math.max(w, 1);
      const ny = (this.y - cy) / Math.max(h, 1);
      const harmonicAngle =
        Math.sin(ny * 7.2 + time * 0.0009) * 1.7 +
        Math.cos(nx * 6.4 - time * 0.00075) * 1.7 +
        Math.atan2(dyC, dxC) +
        HALF_PI * 1.04;
      const n = (noise(this.x * 0.0018, this.y * 0.0018, time * 0.00024) - 0.5) * 0.85;
      ax += Math.cos(harmonicAngle + n) * 0.1 * this.depth;
      ay += Math.sin(harmonicAngle + n) * 0.1 * this.depth;

      // Soft harmonic pull toward nested orbital bands
      const targetR = Math.min(w, h) * (0.14 + ((this.seed % 100) / 100) * 0.34);
      const radialErr = distC - targetR;
      ax -= (dxC / distC) * radialErr * 0.0007;
      ay -= (dyC / distC) * radialErr * 0.0007;
    }

    // 2. Interactive Cursor Field (Fluid Swirl Wake + Gravitational Singularity on Hold)
    if (pointer.active) {
      const mdx = pointer.x - this.x;
      const mdy = pointer.y - this.y;
      const mDistSq = mdx * mdx + mdy * mdy;

      if (pointer.holding && pointer.charge > 0.06) {
        // Gravitational Singularity & Accretion Vortex
        const wellRadius = Math.min(w, h) * (0.44 + pointer.charge * 0.24);
        if (mDistSq < wellRadius * wellRadius) {
          const mDist = Math.sqrt(mDistSq) + 1;
          const falloff = Math.pow(1 - mDist / wellRadius, 1.35);
          const nx = mdx / mDist;
          const ny = mdy / mDist;

          // Event horizon core radius keeps particles orbiting cleanly instead of collapsing to NaN
          const horizon = 26 + pointer.charge * 18;
          const radialForce = mDist > horizon
            ? (0.34 + pointer.charge * 0.65) * falloff
            : -0.45 * (1 - mDist / horizon);

          const swirlForce = (0.42 + pointer.charge * 0.82) * falloff;

          ax += nx * radialForce - ny * swirlForce;
          ay += ny * radialForce + nx * swirlForce;

          this.energy = Math.min(1.0, this.energy + falloff * (0.045 + pointer.charge * 0.08));
        }
      } else {
        // Cursor Glide: graceful gravitational orbit + fluid wake dragging
        const influenceRadius = 215 + Math.min(pointer.speed * 4.5, 110);
        if (mDistSq < influenceRadius * influenceRadius) {
          const mDist = Math.sqrt(mDistSq) + 1;
          const falloff = 1 - mDist / influenceRadius;
          const smoothFalloff = falloff * falloff;
          const nx = mdx / mDist;
          const ny = mdy / mDist;

          // Gentle orbital sheath around cursor (attract from mid-range, cushion very close)
          const idealOrbit = 58;
          const radialSign = mDist > idealOrbit ? 0.14 : -0.22;
          ax += nx * radialSign * smoothFalloff;
          ay += ny * radialSign * smoothFalloff;

          // Delicate vortex spin around pointer
          const spin = 0.19 * smoothFalloff * this.orbitSign;
          ax += -ny * spin;
          ay += nx * spin;

          // Fluid wake impulse from cursor movement velocity
          ax += pointer.vx * 0.024 * smoothFalloff;
          ay += pointer.vy * 0.024 * smoothFalloff;

          this.energy = Math.min(1.0, this.energy + smoothFalloff * (0.03 + pointer.speed * 0.005));
        }
      }
    }

    // 3. Supernova Shockwave Wavefront Interaction
    for (let i = 0; i < shockwaves.length; i++) {
      const sw = shockwaves[i];
      const sdx = this.x - sw.x;
      const sdy = this.y - sw.y;
      const sDist = Math.hypot(sdx, sdy) + 0.001;
      const bandDelta = Math.abs(sDist - sw.radius);
      const bandWidth = sw.bandWidth;

      if (bandDelta < bandWidth) {
        const waveFactor = (1 - bandDelta / bandWidth) * sw.strength * sw.life;
        const nx = sdx / sDist;
        const ny = sdy / sDist;
        // Passing ripple & swirl: excites stars as the wavefront sweeps past without snowplowing a hole
        ax += (nx * 0.24 - ny * 0.24 * sw.spin) * waveFactor;
        ay += (ny * 0.24 + nx * 0.24 * sw.spin) * waveFactor;
        this.energy = Math.min(1.0, this.energy + waveFactor * 0.48);
      }
    }

    // Integrate velocity with smooth cosmic drag
    this.vx = (this.vx + ax) * 0.968;
    this.vy = (this.vy + ay) * 0.968;

    const speed = Math.hypot(this.vx, this.vy);
    const dynamicCap = this.maxSpeed * (1 + this.energy * 1.9);
    if (speed > dynamicCap) {
      const scale = dynamicCap / speed;
      this.vx *= scale;
      this.vy *= scale;
    }

    this.x += this.vx;
    this.y += this.vy;

    // Gentle energy cooling
    this.energy *= 0.972;

    // Soft margin wrap without streak artifacts across the screen
    const pad = 36;
    let wrapped = false;
    if (this.x < -pad) { this.x = w + pad; wrapped = true; }
    else if (this.x > w + pad) { this.x = -pad; wrapped = true; }
    if (this.y < -pad) { this.y = h + pad; wrapped = true; }
    else if (this.y > h + pad) { this.y = -pad; wrapped = true; }
    if (wrapped) {
      this.px = this.x;
      this.py = this.y;
      this.clearTrail();
    } else {
      this.pushTrail();
    }
  }

  getLifeAlpha() {
    const fadeIn = Math.min(1, this.age / 42);
    const fadeOut = Math.min(1, (this.maxAge - this.age) / 68);
    return fadeIn * fadeOut;
  }
}

class Shockwave {
  constructor(x, y, power, palette) {
    this.x = x;
    this.y = y;
    this.power = power;
    this.radius = 12;
    this.maxRadius = Math.min(width, height) * (0.44 + power * 0.3);
    this.speed = 8.5 + power * 4.5;
    this.bandWidth = 34 + power * 18;
    this.strength = 0.72 + power * 0.65;
    this.life = 1.0;
    this.spin = random() < 0.5 ? 1 : -1;
    this.seed = random(100);
    this.ringA = [...palette.burstRingA];
    this.ringB = [...palette.burstRingB];
  }

  update() {
    this.radius += this.speed;
    this.speed = Math.max(6.2, this.speed * 0.986);
    this.life = Math.max(0, 1 - this.radius / this.maxRadius);
    return this.life > 0.01;
  }

  draw(ctx, time) {
    const alpha = Math.pow(this.life, 1.45);
    if (alpha <= 0.005) return;

    ctx.save();
    ctx.globalCompositeOperation = 'lighter';

    // Soft plasma wavefront band
    const [r1, g1, b1] = this.ringA.map(Math.round);
    const [r2, g2, b2] = this.ringB.map(Math.round);

    const innerR = Math.max(1, this.radius - 26);
    const outerR = this.radius + 14;
    const grad = ctx.createRadialGradient(this.x, this.y, innerR, this.x, this.y, outerR);
    grad.addColorStop(0.0, `rgba(${r2}, ${g2}, ${b2}, 0)`);
    grad.addColorStop(0.58, `rgba(${r1}, ${g1}, ${b1}, ${(alpha * 0.24).toFixed(3)})`);
    grad.addColorStop(0.84, `rgba(255, 248, 236, ${(alpha * 0.34).toFixed(3)})`);
    grad.addColorStop(1.0, `rgba(${r2}, ${g2}, ${b2}, 0)`);

    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(this.x, this.y, outerR, 0, TWO_PI);
    ctx.fill();

    // Organic shimmering hairline ring (subtle Perlin ripple so it feels alive, not mechanical)
    const steps = 64;
    ctx.beginPath();
    for (let i = 0; i <= steps; i++) {
      const a = (i / steps) * TWO_PI;
      const ripple = (noise(Math.cos(a) * 1.8 + this.seed, Math.sin(a) * 1.8 + time * 0.01) - 0.5) * 14 * this.life;
      const rad = this.radius + ripple;
      const px = this.x + Math.cos(a) * rad;
      const py = this.y + Math.sin(a) * rad;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.strokeStyle = `rgba(${r1}, ${g1}, ${b1}, ${(alpha * 0.58).toFixed(3)})`;
    ctx.lineWidth = 1.4 + this.power * 0.9;
    ctx.stroke();

    // Secondary chromatic echo ring slightly behind
    if (this.radius > 22) {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius * 0.86, 0, TWO_PI);
      ctx.strokeStyle = `rgba(${r2}, ${g2}, ${b2}, ${(alpha * 0.28).toFixed(3)})`;
      ctx.lineWidth = 1.0;
      ctx.stroke();
    }

    ctx.restore();
  }
}

class StardustSpark {
  constructor(x, y, vx, vy, colorRgb, size, maxLife, curl = 0) {
    this.x = x;
    this.y = y;
    this.px = x;
    this.py = y;
    this.vx = vx;
    this.vy = vy;
    this.color = [...colorRgb];
    this.size = size;
    this.life = 1.0;
    this.decay = 1 / maxLife;
    this.curl = curl;
    this.twinkleOffset = random(TWO_PI);
    this.trailLen = 12;
    this.trailX = new Float32Array(this.trailLen);
    this.trailY = new Float32Array(this.trailLen);
    this.trailX[0] = x;
    this.trailY[0] = y;
    this.trailCount = 1;
  }

  update() {
    this.px = this.x;
    this.py = this.y;

    // Subtle spiral curl for elegant firework-like supernova filaments
    if (this.curl !== 0) {
      const cosC = Math.cos(this.curl);
      const sinC = Math.sin(this.curl);
      const nvx = this.vx * cosC - this.vy * sinC;
      const nvy = this.vx * sinC + this.vy * cosC;
      this.vx = nvx;
      this.vy = nvy;
    }

    this.vx *= 0.964;
    this.vy *= 0.964;
    this.x += this.vx;
    this.y += this.vy;

    const maxIdx = Math.min(this.trailCount, this.trailLen - 1);
    for (let i = maxIdx; i > 0; i--) {
      this.trailX[i] = this.trailX[i - 1];
      this.trailY[i] = this.trailY[i - 1];
    }
    this.trailX[0] = this.x;
    this.trailY[0] = this.y;
    if (this.trailCount < this.trailLen) this.trailCount++;

    this.life -= this.decay;
    return this.life > 0;
  }
}
