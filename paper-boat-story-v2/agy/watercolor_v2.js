// watercolor_v2.js
// Studio-grade procedural watercolor painting engine for HTML5 Canvas 2D
// Features: Real landscape water reflection, 3-value painterly botanical canopies,
// organic brush strokes, global domain-warped wet-paper physics, coffee-ring edge darkening,
// and Arches 300gsm cold-press paper granulation (fast single-pass pixel physics!)

export class SeededRNG {
  constructor(seed = 12345) { this.s = seed >>> 0; }
  next() {
    let t = (this.s += 0x6D2B79F5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  range(min, max) { return min + this.next() * (max - min); }
  gauss(mean = 0, std = 1) {
    let u = 0, v = 0;
    while (u === 0) u = this.next();
    while (v === 0) v = this.next();
    return mean + std * Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
  }
  pick(arr) { return arr[Math.floor(this.next() * arr.length)]; }
}

export class ValueNoise2D {
  constructor(seed = 42, size = 256) {
    this.size = size;
    this.mask = size - 1;
    this.grid = new Float32Array(size * size);
    const rng = new SeededRNG(seed);
    for (let i = 0; i < this.grid.length; i++) this.grid[i] = rng.next();
  }
  sample(x, y) {
    const xi = Math.floor(x), yi = Math.floor(y);
    const xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf);
    const v = yf * yf * (3 - 2 * yf);
    const x0 = xi & this.mask, x1 = (xi + 1) & this.mask;
    const y0 = yi & this.mask, y1 = (yi + 1) & this.mask;
    const a = this.grid[y0 * this.size + x0];
    const b = this.grid[y0 * this.size + x1];
    const c = this.grid[y1 * this.size + x0];
    const d = this.grid[y1 * this.size + x1];
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  }
  fbm(x, y, octaves = 4) {
    let sum = 0, amp = 0.5, freq = 1.0, norm = 0;
    for (let i = 0; i < octaves; i++) {
      sum += amp * this.sample(x * freq, y * freq);
      norm += amp;
      freq *= 2.02;
      amp *= 0.5;
    }
    return sum / norm;
  }
}

export function hexToRgb(hex) {
  const n = parseInt(hex.replace('#', ''), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
export function rgba(hex, a = 1) {
  const [r, g, b] = hexToRgb(hex);
  return `rgba(${r},${g},${b},${a})`;
}

export function sampleCubic(p0, p1, p2, p3, steps = 14) {
  const pts = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps, u = 1 - t;
    pts.push([
      u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
      u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1],
    ]);
  }
  return pts;
}

export function sampleBezierShape(segs, stepsPerSeg = 12) {
  const pts = [];
  for (const [p0, c1, c2, p3] of segs) {
    const s = sampleCubic(p0, c1, c2, p3, stepsPerSeg);
    for (let i = 0; i < s.length - 1; i++) pts.push(s[i]);
  }
  return pts;
}

export function ellipsePts(cx, cy, rx, ry, segs = 20, rot = 0) {
  const pts = [], cos = Math.cos(rot), sin = Math.sin(rot);
  for (let i = 0; i < segs; i++) {
    const a = (i / segs) * Math.PI * 2;
    const x = Math.cos(a) * rx, y = Math.sin(a) * ry;
    pts.push([cx + x * cos - y * sin, cy + x * sin + y * cos]);
  }
  return pts;
}

export function deformPts(pts, rng, iters = 2, variance = 0.12, closed = true) {
  let cur = pts.map(p => [p[0], p[1]]);
  let v = variance;
  for (let it = 0; it < iters; it++) {
    const next = [];
    const n = cur.length, count = closed ? n : n - 1;
    for (let i = 0; i < count; i++) {
      const a = cur[i], b = cur[(i + 1) % n];
      next.push(a);
      const dx = b[0] - a[0], dy = b[1] - a[1], d = Math.hypot(dx, dy);
      if (d > 2.5) {
        const off = rng.gauss(0, d * v);
        next.push([(a[0] + b[0]) * 0.5 - (dy / d) * off, (a[1] + b[1]) * 0.5 + (dx / d) * off]);
      }
    }
    if (!closed) next.push(cur[n - 1]);
    cur = next;
    v *= 0.56;
  }
  return cur;
}

export function traceSmooth(ctx, pts, closed = true) {
  if (pts.length < 2) return;
  ctx.beginPath();
  if (closed) {
    const last = pts[pts.length - 1], first = pts[0];
    ctx.moveTo((last[0] + first[0]) * 0.5, (last[1] + first[1]) * 0.5);
    for (let i = 0; i < pts.length; i++) {
      const c = pts[i], n = pts[(i + 1) % pts.length];
      ctx.quadraticCurveTo(c[0], c[1], (c[0] + n[0]) * 0.5, (c[1] + n[1]) * 0.5);
    }
    ctx.closePath();
  } else {
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length - 1; i++) {
      ctx.quadraticCurveTo(pts[i][0], pts[i][1], (pts[i][0] + pts[i + 1][0]) * 0.5, (pts[i][1] + pts[i + 1][1]) * 0.5);
    }
    ctx.lineTo(pts[pts.length - 1][0], pts[pts.length - 1][1]);
  }
}

export class WatercolorStudio {
  constructor(canvas, seed = 2026) {
    this.canvas = canvas;
    this.w = canvas.width;
    this.h = canvas.height;
    this.ctx = canvas.getContext('2d', { willReadFrequently: true });
    this.rng = new SeededRNG(seed);
    this.noise1 = new ValueNoise2D(seed + 17, 256);
    this.noise2 = new ValueNoise2D(seed + 193, 256);

    // Clean warm ivory Arches paper base
    this.ctx.fillStyle = '#FCF9F1';
    this.ctx.fillRect(0, 0, this.w, this.h);
  }

  // Fast, juicy layered watercolor wash (no per-call getImageData overhead!)
  wash(pts, opts = {}) {
    const {
      color = '#7CC6D4',
      color2 = null,
      alpha = 0.60,
      layers = 7,
      variance = 0.08,
      iters = 2,
      blur = 1.0,
      composite = 'multiply',
      rimStroke = 0.22,
    } = opts;

    const ctx = this.ctx;
    ctx.save();
    ctx.globalCompositeOperation = composite;

    const c1 = hexToRgb(color);
    const c2 = color2 ? hexToRgb(color2) : c1;
    const perA = Math.min(0.42, (alpha / layers) * 1.55);

    for (let i = 0; i < layers; i++) {
      const poly = variance > 0.005 ? deformPts(pts, this.rng, iters, variance, true) : pts;
      const t = i / Math.max(1, layers - 1);
      const r = Math.round(c1[0] * (1 - t) + c2[0] * t);
      const g = Math.round(c1[1] * (1 - t) + c2[1] * t);
      const b = Math.round(c1[2] * (1 - t) + c2[2] * t);
      traceSmooth(ctx, poly, true);
      ctx.fillStyle = `rgba(${r},${g},${b},${perA})`;
      ctx.fill();
    }

    // Subtle dried watercolor edge-pooling rim
    if (rimStroke > 0) {
      const rimPoly = variance > 0.005 ? deformPts(pts, this.rng, iters, variance * 0.65, true) : pts;
      traceSmooth(ctx, rimPoly, true);
      ctx.strokeStyle = rgba(color2 || color, alpha * rimStroke);
      ctx.lineWidth = 1.6;
      ctx.stroke();
    }
    ctx.restore();
  }

  // Opaque-ish paper-reserve / gouache base (keeps foreground subjects luminous over background)
  reserve(pts, color = '#FCF9F1', alpha = 0.95, blur = 0) {
    const ctx = this.ctx;
    ctx.save();
    ctx.globalCompositeOperation = 'source-over';
    traceSmooth(ctx, pts, true);
    ctx.fillStyle = rgba(color, alpha);
    ctx.fill();
    ctx.restore();
  }

  // Smooth atmospheric radial wash (sky glow, sunlight bloom, soft shadows)
  glow(cx, cy, rx, ry, color, alpha = 0.40, composite = 'multiply', rot = 0) {
    const [r, g, b] = hexToRgb(color);
    const ctx = this.ctx;
    ctx.save();
    ctx.globalCompositeOperation = composite;
    ctx.translate(cx, cy);
    ctx.rotate(rot);
    ctx.scale(1, ry / Math.max(1, rx));
    const grad = ctx.createRadialGradient(0, 0, 0, 0, 0, rx);
    grad.addColorStop(0, `rgba(${r},${g},${b},${alpha})`);
    grad.addColorStop(0.55, `rgba(${r},${g},${b},${alpha * 0.48})`);
    grad.addColorStop(1, `rgba(${r},${g},${b},0)`);
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(0, 0, rx, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  // Organic tapered watercolor brush stroke (leaves, grass blades, branches, hair locks)
  stroke(points, opts = {}) {
    const {
      color = '#5CA456',
      width = 8,
      alpha = 0.65,
      taperStart = 0.3,
      taperEnd = 0.04,
      composite = 'multiply',
      blur = 0.5,
      rimStroke = 0.18,
    } = opts;
    if (points.length < 2) return;
    const left = [], right = [];
    for (let i = 0; i < points.length; i++) {
      const t = i / (points.length - 1);
      const p = points[i];
      const prev = points[Math.max(0, i - 1)];
      const next = points[Math.min(points.length - 1, i + 1)];
      const dx = next[0] - prev[0], dy = next[1] - prev[1];
      const len = Math.hypot(dx, dy) || 1;
      const nx = -dy / len, ny = dx / len;
      const bell = Math.sin(t * Math.PI);
      const w = width * 0.5 * ((taperStart * (1 - t) + taperEnd * t) * 0.35 + bell * 0.88);
      left.push([p[0] + nx * w, p[1] + ny * w]);
      right.unshift([p[0] - nx * w, p[1] - ny * w]);
    }
    this.wash([...left, ...right], {
      color,
      alpha,
      layers: 3,
      variance: 0.05,
      iters: 1,
      blur,
      composite,
      rimStroke,
    });
  }

  // Expressive hand-drawn sepia/indigo colored-pencil line (variable pressure & gentle sketch feel)
  pencil(points, opts = {}) {
    const {
      color = '#6D5242',
      width = 1.4,
      alpha = 0.52,
      jitter = 0.45,
      passes = 2,
    } = opts;
    const [r, g, b] = hexToRgb(color);
    const ctx = this.ctx;
    ctx.save();
    ctx.globalCompositeOperation = 'multiply';
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    for (let pass = 0; pass < passes; pass++) {
      const sub = [];
      for (let i = 0; i < points.length - 1; i++) {
        const a = points[i], c = points[i + 1];
        const steps = Math.max(2, Math.ceil(Math.hypot(c[0] - a[0], c[1] - a[1]) / 5));
        for (let s = 0; s < steps; s++) {
          const t = s / steps;
          sub.push([
            a[0] + (c[0] - a[0]) * t + this.rng.gauss(0, jitter * (pass ? 0.9 : 0.45)),
            a[1] + (c[1] - a[1]) * t + this.rng.gauss(0, jitter * (pass ? 0.9 : 0.45)),
          ]);
        }
      }
      sub.push(points[points.length - 1]);
      for (let i = 0; i < sub.length - 1; i++) {
        const t = i / Math.max(1, sub.length - 1);
        const fade = Math.sin(Math.min(1, t * 6) * Math.PI * 0.5) * Math.sin(Math.min(1, (1 - t) * 6) * Math.PI * 0.5);
        ctx.strokeStyle = `rgba(${r},${g},${b},${alpha * (pass ? 0.32 : 0.68) * fade})`;
        ctx.lineWidth = Math.max(0.5, width * (pass ? 0.72 : 1.0) * (0.8 + 0.35 * Math.sin(t * Math.PI)));
        ctx.beginPath();
        ctx.moveTo(sub[i][0], sub[i][1]);
        ctx.lineTo(sub[i + 1][0], sub[i + 1][1]);
        ctx.stroke();
      }
    }
    ctx.restore();
  }

  // ============================================================================
  // PAINTERLY ENVIRONMENT BUILDERS (Ghibli / Classic Picture-Book Watercolor!)
  // ============================================================================

  // 1. Luminous Sky with Soft Hand-Painted Watercolor Clouds
  paintSky(horizonY, opts = {}) {
    const {
      topColor = '#8CCAE6',
      midColor = '#CBEAF5',
      horizonColor = '#FFF3CC',
      sunX = 1280,
      sunY = 140,
      sunColor = '#FFE28A',
      cloudCount = 4,
    } = opts;

    const ctx = this.ctx;
    ctx.save();
    ctx.globalCompositeOperation = 'multiply';
    const grad = ctx.createLinearGradient(0, 0, 0, horizonY + 40);
    grad.addColorStop(0, rgba(topColor, 0.72));
    grad.addColorStop(0.52, rgba(midColor, 0.52));
    grad.addColorStop(1, rgba(horizonColor, 0.48));
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, this.w, horizonY + 40);
    ctx.restore();

    // Warm sun atmospheric halo
    this.glow(sunX, sunY, 440, 260, sunColor, 0.50, 'multiply');
    this.glow(sunX, sunY, 260, 160, '#FFFDF5', 0.78, 'screen');

    // Soft seamless Miyazaki-style watercolor cumulus clouds (merged offscreen so zero circle overlaps!)
    const cloudCanv = document.createElement('canvas');
    cloudCanv.width = this.w;
    cloudCanv.height = horizonY + 20;
    const cctx = cloudCanv.getContext('2d');

    for (let i = 0; i < cloudCount; i++) {
      const cx = this.rng.range(180, this.w - 180);
      const cy = this.rng.range(62, horizonY * 0.50);
      const cw = this.rng.range(150, 270);
      const ch = this.rng.range(38, 66);

      cctx.clearRect(0, 0, cloudCanv.width, cloudCanv.height);
      const puffs = 7;
      const puffList = [];
      for (let p = 0; p < puffs; p++) {
        const u = p / (puffs - 1);
        const px = cx + (u - 0.5) * cw * 1.1 + this.rng.range(-12, 12);
        const py = cy - Math.sin(u * Math.PI) * ch * 0.62 + this.rng.range(-6, 6);
        const prx = cw * this.rng.range(0.18, 0.30) * (0.7 + 0.5 * Math.sin(u * Math.PI));
        const pry = ch * this.rng.range(0.48, 0.85) * (0.7 + 0.45 * Math.sin(u * Math.PI));
        puffList.push([px, py, prx, pry]);
      }

      // Draw unified opaque cream-white cloud silhouette on offscreen canvas
      cctx.fillStyle = '#FFFDF7';
      for (const [px, py, prx, pry] of puffList) {
        traceSmooth(cctx, deformPts(ellipsePts(px, py, prx, pry, 14), this.rng, 1, 0.07), true);
        cctx.fill();
      }
      // Paint soft cool lavender-blue underside shading clipped inside the unified cloud!
      cctx.save();
      cctx.globalCompositeOperation = 'source-atop';
      const uGrad = cctx.createLinearGradient(0, cy - ch, 0, cy + ch * 0.55);
      uGrad.addColorStop(0, 'rgba(255,253,245,0)');
      uGrad.addColorStop(0.62, 'rgba(180,202,228,0.10)');
      uGrad.addColorStop(1, 'rgba(155,182,216,0.34)');
      cctx.fillStyle = uGrad;
      cctx.fillRect(0, 0, cloudCanv.width, cloudCanv.height);
      cctx.restore();

      // Composite unified fluffy cloud onto sky
      ctx.save();
      ctx.globalAlpha = 0.82;
      ctx.drawImage(cloudCanv, 0, 0);
      ctx.restore();
    }
  }

  // 2. Layered Atmospheric Distant Hills / Wooded Horizon (Instant 3D Depth!)
  paintDistantHills(horizonY, layers = []) {
    for (const layer of layers) {
      const { color, color2, alpha = 0.55, amp = 55, yOff = 0, freq = 0.0028, phase = 0, blur = 2.5 } = layer;
      const pts = [[-40, horizonY + 30]];
      const steps = 28;
      for (let i = 0; i <= steps; i++) {
        const x = -40 + (i / steps) * (this.w + 80);
        const y = horizonY + yOff
          - Math.abs(Math.sin(x * freq + phase)) * amp
          - Math.sin(x * freq * 2.3 + phase * 1.7) * amp * 0.28
          - this.noise1.sample(x * 0.008 + phase, 1.5) * amp * 0.35;
        pts.push([x, y]);
      }
      pts.push([this.w + 40, horizonY + 30]);
      this.wash(pts, {
        color,
        color2: color2 || color,
        alpha,
        layers: 5,
        variance: 0.04,
        blur,
        rimStroke: 0.14,
      });
    }
  }

  // 3. Organic, Varied Painterly Watercolor Tree (Asymmetric trunks + bushy shoreline base + 3-value canopy!)
  paintTree(baseX, baseY, scale = 1.0, opts = {}) {
    const {
      sunFromRight = true,
      alpha = 0.82,
      shadowCol = '#34755E',
      midCol = '#5EA656',
      lightCol = '#B4D65E',
      sunCol = '#ECE678',
      lean = null,
    } = opts;

    const s = scale;
    const treeLean = lean !== null ? lean : this.rng.range(-28, 28);
    const trunkH = this.rng.range(125, 168) * s;
    const trunkTopX = baseX + treeLean * s;
    const trunkTopY = baseY - trunkH;

    // Asymmetric graceful trunk
    this.stroke([
      [baseX, baseY + 6 * s],
      [baseX + treeLean * 0.42 * s, baseY - trunkH * 0.48],
      [trunkTopX, trunkTopY],
    ], { color: '#7A5D48', width: 20 * s, alpha: alpha * 0.82, taperStart: 0.92, taperEnd: 0.32 });

    // Organic varied branches
    const branches = [
      [[trunkTopX - 4 * s, trunkTopY + 34 * s], [trunkTopX - 52 * s, trunkTopY - 12 * s], [trunkTopX - 96 * s, trunkTopY - 38 * s]],
      [[trunkTopX + 4 * s, trunkTopY + 22 * s], [trunkTopX + 48 * s, trunkTopY - 26 * s], [trunkTopX + 98 * s, trunkTopY - 42 * s]],
      [[trunkTopX, trunkTopY + 12 * s], [trunkTopX + treeLean * 0.3 * s, trunkTopY - 48 * s], [trunkTopX - 14 * s, trunkTopY - 92 * s]],
    ];
    for (const br of branches) {
      this.stroke(br, { color: '#8A6A52', width: 9 * s, alpha: alpha * 0.72, taperStart: 0.78, taperEnd: 0.14 });
    }

    // Lush varied asymmetric canopy clusters
    const sunDir = sunFromRight ? 1 : -1;
    const clusters = [
      { dx: -82 + treeLean * 0.5, dy: -trunkH / s - 22, rx: 86, ry: 58 },
      { dx: 4 + treeLean * 0.8, dy: -trunkH / s - 68, rx: 104, ry: 66 },
      { dx: 88 + treeLean * 0.6, dy: -trunkH / s - 26, rx: 88, ry: 56 },
      { dx: -32 + treeLean * 0.5, dy: -trunkH / s + 2, rx: 74, ry: 46 },
      { dx: 48 + treeLean * 0.6, dy: -trunkH / s + 4, rx: 76, ry: 48 },
    ];

    // Pass A: Soft unifying canopy wash
    for (const c of clusters) {
      this.wash(ellipsePts(baseX + c.dx * s, baseY + c.dy * s, c.rx * s, c.ry * s, 14), {
        color: midCol, color2: lightCol, alpha: alpha * 0.38, layers: 4, variance: 0.18, rimStroke: 0.12,
      });
    }
    // Pass B: Deep viridian-teal shadow undersides
    for (const c of clusters) {
      const sx = baseX + (c.dx - sunDir * 18) * s;
      const sy = baseY + (c.dy + 16) * s;
      for (let i = 0; i < 6; i++) {
        const lx = sx + this.rng.gauss(0, c.rx * 0.36 * s);
        const ly = sy + this.rng.gauss(0, c.ry * 0.32 * s);
        this.wash(ellipsePts(lx, ly, this.rng.range(18, 34) * s, this.rng.range(12, 22) * s, 10, this.rng.range(0, 3)), {
          color: shadowCol, alpha: alpha * 0.42, layers: 3, variance: 0.15, rimStroke: 0.16,
        });
      }
    }
    // Pass C: Sunlit golden-chartreuse crown leaves
    for (const c of clusters) {
      const lx0 = baseX + (c.dx + sunDir * 20) * s;
      const ly0 = baseY + (c.dy - 14) * s;
      for (let i = 0; i < 8; i++) {
        const lx = lx0 + this.rng.gauss(0, c.rx * 0.42 * s);
        const ly = ly0 + this.rng.gauss(0, c.ry * 0.36 * s);
        this.wash(ellipsePts(lx, ly, this.rng.range(14, 28) * s, this.rng.range(9, 18) * s, 10, this.rng.range(0, 3)), {
          color: i < 3 ? sunCol : lightCol, alpha: alpha * 0.50, layers: 3, variance: 0.15, rimStroke: 0.18,
        });
      }
    }

    // Lush bushes nestled organically around the base of the trunk (breaks straight shoreline!)
    for (let b = -1; b <= 1; b++) {
      const bx = baseX + b * 46 * s + this.rng.range(-12, 12) * s;
      const by = baseY - this.rng.range(4, 16) * s;
      this.wash(ellipsePts(bx, by, this.rng.range(28, 48) * s, this.rng.range(16, 28) * s, 12), {
        color: b === sunDir ? lightCol : midCol,
        color2: shadowCol,
        alpha: alpha * 0.58,
        layers: 4,
        variance: 0.16,
        rimStroke: 0.15,
      });
    }
  }

  // 4. SILKY SCANLINE-FREE MIRROR-REFLECTION WATER ENGINE!
  //    Composites reflection cleanly onto an offscreen canvas with ZERO row-overlap stripes!
  paintWaterWithReflection(horizonY, opts = {}) {
    const {
      tintTop = '#9EE0E2',
      tintDeep = '#4D9FC2',
      shadeTint = '#5B88B8',
      sunX = 1280,
      sunWidth = 340,
      sunColor = '#FFD970',
      reflectionAlpha = 0.44,
      rippleAmp = 13,
    } = opts;

    const w = this.w, h = this.h;
    const waterH = h - horizonY;

    // Snapshot upper landscape
    const snap = document.createElement('canvas');
    snap.width = w;
    snap.height = horizonY;
    snap.getContext('2d').drawImage(this.canvas, 0, 0, w, horizonY, 0, 0, w, horizonY);

    // Build seamless, scanline-free rippled reflection on a dedicated offscreen canvas
    const refl = document.createElement('canvas');
    refl.width = w;
    refl.height = waterH;
    const rctx = refl.getContext('2d');
    const sliceH = 2;
    for (let y = 0; y < waterH; y += sliceH) {
      const t = y / waterH;
      const srcY = Math.max(0, Math.min(horizonY - sliceH, horizonY - 2 - Math.floor(y * 0.72)));
      const wave = Math.sin(y * 0.065 + t * 6.5) * (rippleAmp * (0.22 + t * 0.92))
                 + Math.sin(y * 0.17) * (rippleAmp * 0.24);
      // Exact sliceH with source-over => ZERO double-multiply horizontal scanlines!
      rctx.drawImage(snap, 0, srcY, w, sliceH, wave, y, w, sliceH);
    }
    // Fade reflection gently with water depth using destination-in gradient
    rctx.save();
    rctx.globalCompositeOperation = 'destination-in';
    const fadeG = rctx.createLinearGradient(0, 0, 0, waterH);
    fadeG.addColorStop(0, `rgba(255,255,255,${reflectionAlpha * 0.85})`);
    fadeG.addColorStop(0.45, `rgba(255,255,255,${reflectionAlpha})`);
    fadeG.addColorStop(1, `rgba(255,255,255,${reflectionAlpha * 0.42})`);
    rctx.fillStyle = fadeG;
    rctx.fillRect(0, 0, w, waterH);
    rctx.restore();

    const ctx = this.ctx;
    // Base clean paper-bright turquoise-cerulean water wash
    ctx.save();
    const baseGrad = ctx.createLinearGradient(0, horizonY, 0, h);
    baseGrad.addColorStop(0, rgba(tintTop, 0.46));
    baseGrad.addColorStop(0.55, rgba(tintDeep, 0.44));
    baseGrad.addColorStop(1, rgba(shadeTint, 0.52));
    ctx.globalCompositeOperation = 'multiply';
    ctx.fillStyle = baseGrad;
    ctx.fillRect(0, horizonY, w, waterH);
    // Composite the entire silky reflection ONCE with multiply!
    ctx.drawImage(refl, 0, horizonY);
    ctx.restore();

    // Soft organic watercolor current strokes
    for (let i = 0; i < 18; i++) {
      const t = (i + 0.3) / 18;
      const y = horizonY + 18 + t * (waterH - 35) + this.rng.range(-10, 10);
      const x0 = this.rng.range(-80, w * 0.55);
      const len = this.rng.range(260, 680);
      this.stroke([
        [x0, y],
        [x0 + len * 0.33, y + this.rng.range(-8, 8)],
        [x0 + len * 0.66, y + this.rng.range(-8, 8)],
        [x0 + len, y],
      ], {
        color: i % 3 === 0 ? shadeTint : tintDeep,
        width: this.rng.range(10, 24) * (0.5 + t * 0.7),
        alpha: this.rng.range(0.12, 0.24),
        rimStroke: 0.06,
      });
    }

    // Glowing sunlit golden reflection shimmer path on the water
    this.glow(sunX, horizonY + waterH * 0.38, sunWidth, waterH * 0.46, sunColor, 0.44, 'multiply', -0.05);
    this.glow(sunX, horizonY + waterH * 0.32, sunWidth * 0.80, waterH * 0.38, '#FFFDF4', 0.64, 'screen', -0.05);

    // Dancing sunlit water sparkles
    for (let i = 0; i < 68; i++) {
      const t = Math.pow(this.rng.next(), 0.75);
      const y = horizonY + 12 + t * (waterH - 30);
      const spread = sunWidth * (0.35 + t * 0.85);
      const x = sunX + this.rng.gauss(0, spread * 0.45);
      const rx = this.rng.range(4, 22) * (0.45 + t * 0.85);
      const ry = Math.max(1.2, rx * this.rng.range(0.14, 0.28));
      this.reserve(ellipsePts(x, y, rx, ry, 10), '#FFFFFF', this.rng.range(0.45, 0.90));
    }

    // Soft sunlit atmospheric mist along the far shoreline so it blends poetically (no harsh horizontal bar!)
    this.glow(w * 0.5, horizonY + 2, w * 0.65, 26, '#FFFDF5', 0.46, 'screen');
  }

  // 5. Lush Hand-Painted Grass Blades & Wildflower Meadow Details
  paintGrassTuft(x, y, count = 9, height = 55, opts = {}) {
    const {
      colors = ['#5CA654', '#8AC75A', '#3D8453', '#C5DD62'],
      lean = 0.15,
      alpha = 0.70,
      width = 4.5,
    } = opts;
    for (let i = 0; i < count; i++) {
      const bx = x + this.rng.range(-18, 18);
      const h = height * this.rng.range(0.55, 1.25);
      const b = (lean + this.rng.range(-0.35, 0.35)) * h;
      this.stroke([
        [bx, y],
        [bx + b * 0.35, y - h * 0.45],
        [bx + b, y - h],
      ], {
        color: this.rng.pick(colors),
        width: width * this.rng.range(0.65, 1.3),
        alpha: alpha * this.rng.range(0.7, 1.05),
        taperStart: 0.75,
        taperEnd: 0.02,
        blur: 0.3,
        rimStroke: 0.12,
      });
    }
  }

  // 6. Delicate Water Ripples
  ripple(cx, cy, rx, ry, opts = {}) {
    const { light = '#FFFFFF', shadow = '#468BB0', alpha = 0.70, thickness = 2.0 } = opts;
    const drawRing = (yOff, col, a, w, comp) => {
      const ctx = this.ctx;
      ctx.save();
      ctx.globalCompositeOperation = comp;
      const [r, g, b] = hexToRgb(col);
      const segs = 44;
      for (let i = 0; i < segs; i++) {
        const a1 = (i / segs) * Math.PI * 2, a2 = ((i + 1) / segs) * Math.PI * 2;
        const gap = Math.sin(a1 * 2 + 0.5) * 0.35 + 0.65;
        if (gap < 0.36) continue;
        ctx.strokeStyle = `rgba(${r},${g},${b},${a * gap})`;
        ctx.lineWidth = w * (0.65 + 0.5 * Math.abs(Math.sin(a1)));
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(a1) * rx, cy + yOff + Math.sin(a1) * ry);
        ctx.lineTo(cx + Math.cos(a2) * rx, cy + yOff + Math.sin(a2) * ry);
        ctx.stroke();
      }
      ctx.restore();
    };
    drawRing(1.8, shadow, alpha * 0.42, thickness * 1.15, 'multiply');
    drawRing(0, light, alpha * 0.88, thickness, 'source-over');
  }

  // 7. Restrained Watercolor Pigment Splatter
  splatter(cx, cy, radius, count, color, alpha = 0.38) {
    const [r, g, b] = hexToRgb(color);
    const ctx = this.ctx;
    ctx.save();
    ctx.globalCompositeOperation = 'multiply';
    for (let i = 0; i < count; i++) {
      const a = this.rng.range(0, Math.PI * 2);
      const d = Math.pow(this.rng.next(), 0.72) * radius;
      const rad = this.rng.range(0.9, 3.2);
      ctx.fillStyle = `rgba(${r},${g},${b},${alpha * this.rng.range(0.4, 1.0)})`;
      ctx.beginPath();
      ctx.ellipse(cx + Math.cos(a) * d, cy + Math.sin(a) * d, rad, rad * this.rng.range(0.7, 1.3), a, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  // ============================================================================
  // SINGLE-PASS OPTICAL WATERCOLOR PAPER & PIGMENT PHYSICS SHADER!
  //   1) Subtle wet-paper domain warp (~1.4px) so ALL edges organically follow paper fibers
  //   2) Cold-press 300gsm Arches paper tooth & granulation
  //   3) Subtle global coffee-ring pigment edge pooling
  //   4) Warm poetic storybook light & organic deckle paper margin
  // ============================================================================
  applyWatercolorPhysics(opts = {}) {
    const {
      warpStrength = 1.35,
      paperGrain = 0.095,
      granulation = 0.11,
      warmth = 0.06,
      marginFade = true,
    } = opts;

    const w = this.w, h = this.h;
    const srcImg = this.ctx.getImageData(0, 0, w, h);
    const src = srcImg.data;
    const dstImg = this.ctx.createImageData(w, h);
    const dst = dstImg.data;

    for (let y = 0; y < h; y++) {
      const row = y * w;
      for (let x = 0; x < w; x++) {
        // Multi-scale Arches cold-press paper tooth (valleys & cotton fibers)
        const dimple = this.noise1.fbm(x * 0.085, y * 0.085, 3);
        const fine = this.noise2.sample(x * 0.34, y * 0.34);
        const tooth = dimple * 0.65 + fine * 0.35; // 0..1

        // Subtle organic wet-paper domain warp (breaks digital smoothness!)
        const wx = (this.noise1.sample(x * 0.045, y * 0.045) - 0.5) * 2.0 * warpStrength;
        const wy = (this.noise2.sample(x * 0.045 + 31.7, y * 0.045 + 17.3) - 0.5) * 2.0 * warpStrength;

        const sx = Math.max(0, Math.min(w - 1, Math.round(x + wx)));
        const sy = Math.max(0, Math.min(h - 1, Math.round(y + wy)));
        const sp = (sy * w + sx) * 4;

        let r = src[sp];
        let g = src[sp + 1];
        let b = src[sp + 2];

        // Pigment density estimate (darker = heavier pigment = stronger granulation in paper valleys!)
        const lum = (r * 0.299 + g * 0.587 + b * 0.114) / 255;
        const pigment = 1.0 - lum;

        // Paper tooth relief + pigment granulation (pigment settles into valleys where tooth < 0.5)
        const paperMod = 1.0 + (tooth - 0.5) * paperGrain;
        const granMod = 1.0 - (0.5 - tooth) * pigment * granulation * 1.8;
        const totalMod = paperMod * granMod;

        r = Math.max(0, Math.min(255, r * totalMod));
        g = Math.max(0, Math.min(255, g * totalMod * 0.998));
        b = Math.max(0, Math.min(255, b * totalMod * 0.992));

        const dp = (row + x) * 4;
        dst[dp] = r;
        dst[dp + 1] = g;
        dst[dp + 2] = b;
        dst[dp + 3] = 255;
      }
    }
    this.ctx.putImageData(dstImg, 0, 0);

    // Subtle warm sunlit storybook atmosphere
    if (warmth > 0) {
      this.ctx.save();
      this.ctx.globalCompositeOperation = 'soft-light';
      this.ctx.fillStyle = `rgba(255, 240, 200, ${warmth})`;
      this.ctx.fillRect(0, 0, w, h);
      this.ctx.restore();
    }

    // Soft storybook cream-paper margin vignette
    if (marginFade) {
      this.ctx.save();
      const grad = this.ctx.createRadialGradient(
        w * 0.5, h * 0.5, Math.min(w, h) * 0.45,
        w * 0.5, h * 0.5, Math.hypot(w, h) * 0.58
      );
      grad.addColorStop(0, 'rgba(252,249,241,0)');
      grad.addColorStop(0.82, 'rgba(252,249,241,0.10)');
      grad.addColorStop(1, 'rgba(252,249,241,0.72)');
      this.ctx.fillStyle = grad;
      this.ctx.fillRect(0, 0, w, h);
      this.ctx.restore();
    }
  }
}
