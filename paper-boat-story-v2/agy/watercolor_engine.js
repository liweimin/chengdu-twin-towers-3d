// watercolor_engine.js
// Luminous, juicy children's picture-book watercolor engine (crisp wet-on-dry edges,
// vibrant transparent glazing, periwinkle shadows, cold-press paper granulation)

export class SeededRNG {
  constructor(seed = 12345) {
    this.s = seed >>> 0;
  }
  next() {
    let t = (this.s += 0x6D2B79F5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  range(min, max) {
    return min + this.next() * (max - min);
  }
  gauss(mean = 0, std = 1) {
    let u = 0, v = 0;
    while (u === 0) u = this.next();
    while (v === 0) v = this.next();
    return mean + std * Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
  }
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
    const xi = Math.floor(x);
    const yi = Math.floor(y);
    const xf = x - xi;
    const yf = y - yi;
    const u = xf * xf * (3 - 2 * xf);
    const v = yf * yf * (3 - 2 * yf);
    const x0 = xi & this.mask;
    const x1 = (xi + 1) & this.mask;
    const y0 = yi & this.mask;
    const y1 = (yi + 1) & this.mask;
    const a = this.grid[y0 * this.size + x0];
    const b = this.grid[y0 * this.size + x1];
    const c = this.grid[y1 * this.size + x0];
    const d = this.grid[y1 * this.size + x1];
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  }
  fbm(x, y, octaves = 4, lacunarity = 2.0, gain = 0.5) {
    let sum = 0, amp = 0.5, freq = 1.0, norm = 0;
    for (let i = 0; i < octaves; i++) {
      sum += amp * this.sample(x * freq, y * freq);
      norm += amp;
      freq *= lacunarity;
      amp *= gain;
    }
    return sum / norm;
  }
}

export function hexToRgb(hex) {
  const clean = hex.replace('#', '');
  const n = parseInt(clean, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

export function rgbStr(r, g, b, a = 1) {
  return `rgba(${Math.round(r)},${Math.round(g)},${Math.round(b)},${a})`;
}

// Sample a cubic bezier curve into smooth dense points (eliminates blocky polygons!)
export function sampleCubic(p0, p1, p2, p3, steps = 14) {
  const pts = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const u = 1 - t;
    const x = u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0];
    const y = u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1];
    pts.push([x, y]);
  }
  return pts;
}

// Build a smooth closed polygon from connected cubic bezier segments:
// segs = [ [p0, c1, c2, p3], ... ]
export function sampleBezierShape(segs, stepsPerSeg = 12) {
  const pts = [];
  for (let s = 0; s < segs.length; s++) {
    const [p0, c1, c2, p3] = segs[s];
    const sampled = sampleCubic(p0, c1, c2, p3, stepsPerSeg);
    for (let i = 0; i < sampled.length - 1; i++) pts.push(sampled[i]);
  }
  return pts;
}

export function deformPolygon(pts, rng, iterations = 3, variance = 0.12, closed = true) {
  let current = pts.map(p => [p[0], p[1]]);
  let v = variance;
  for (let it = 0; it < iterations; it++) {
    const next = [];
    const len = current.length;
    const count = closed ? len : len - 1;
    for (let i = 0; i < count; i++) {
      const p1 = current[i];
      const p2 = current[(i + 1) % len];
      next.push(p1);
      const dx = p2[0] - p1[0];
      const dy = p2[1] - p1[1];
      const dist = Math.hypot(dx, dy);
      if (dist > 2.2) {
        const mx = (p1[0] + p2[0]) * 0.5;
        const my = (p1[1] + p2[1]) * 0.5;
        const nx = -dy / dist;
        const ny = dx / dist;
        const offset = rng.gauss(0, dist * v);
        next.push([mx + nx * offset, my + ny * offset]);
      }
    }
    if (!closed) next.push(current[len - 1]);
    current = next;
    v *= 0.58;
  }
  return current;
}

export function traceSmoothPoly(ctx, pts, closed = true) {
  if (pts.length < 2) return;
  ctx.beginPath();
  if (closed) {
    const last = pts[pts.length - 1];
    const first = pts[0];
    ctx.moveTo((last[0] + first[0]) * 0.5, (last[1] + first[1]) * 0.5);
    for (let i = 0; i < pts.length; i++) {
      const curr = pts[i];
      const next = pts[(i + 1) % pts.length];
      ctx.quadraticCurveTo(curr[0], curr[1], (curr[0] + next[0]) * 0.5, (curr[1] + next[1]) * 0.5);
    }
    ctx.closePath();
  } else {
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length - 1; i++) {
      const mx = (pts[i][0] + pts[i + 1][0]) * 0.5;
      const my = (pts[i][1] + pts[i + 1][1]) * 0.5;
      ctx.quadraticCurveTo(pts[i][0], pts[i][1], mx, my);
    }
    ctx.lineTo(pts[pts.length - 1][0], pts[pts.length - 1][1]);
  }
}

export function ellipsePoints(cx, cy, rx, ry, segments = 20, rot = 0) {
  const pts = [];
  const cos = Math.cos(rot), sin = Math.sin(rot);
  for (let i = 0; i < segments; i++) {
    const a = (i / segments) * Math.PI * 2;
    const x = Math.cos(a) * rx;
    const y = Math.sin(a) * ry;
    pts.push([cx + x * cos - y * sin, cy + x * sin + y * cos]);
  }
  return pts;
}

export class WatercolorCanvas {
  constructor(canvas, seed = 2026) {
    this.canvas = canvas;
    this.w = canvas.width;
    this.h = canvas.height;
    this.ctx = canvas.getContext('2d');
    this.rng = new SeededRNG(seed);
    this.noise = new ValueNoise2D(seed + 77, 256);
    this.noise2 = new ValueNoise2D(seed + 313, 256);

    this.scratch = document.createElement('canvas');
    this.scratch.width = this.w;
    this.scratch.height = this.h;
    this.sctx = this.scratch.getContext('2d', { willReadFrequently: true });

    this.heightMap = new Float32Array(this.w * this.h);
    this.paperCanvas = document.createElement('canvas');
    this.paperCanvas.width = this.w;
    this.paperCanvas.height = this.h;
    this._generatePaper();
  }

  _generatePaper() {
    const w = this.w, h = this.h;
    const pctx = this.paperCanvas.getContext('2d');
    const img = pctx.createImageData(w, h);
    const data = img.data;

    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        // Crisp, bright warm-white 300gsm Arches cold-press watercolor paper (#FDFBF5)
        const dimple = this.noise.fbm(x * 0.085, y * 0.085, 3);
        const fine = this.noise2.sample(x * 0.34, y * 0.34);
        const tooth = dimple * 0.65 + fine * 0.35;
        const idx = y * w + x;
        this.heightMap[idx] = tooth;

        const shade = (tooth - 0.5) * 11;
        const p = idx * 4;
        data[p] = Math.max(0, Math.min(255, 253 + shade));
        data[p + 1] = Math.max(0, Math.min(255, 250 + shade * 0.96));
        data[p + 2] = Math.max(0, Math.min(255, 242 + shade * 0.90));
        data[p + 3] = 255;
      }
    }
    pctx.putImageData(img, 0, 0);
    this.ctx.drawImage(this.paperCanvas, 0, 0);
  }

  // Luminous transparent watercolor wash:
  // Zero gradient-banding, crisp juicy pigment edges, authentic cold-press granulation!
  wash(pts, options = {}) {
    const {
      color = '#7CC6D4',
      color2 = null,
      alpha = 0.65,
      layers = 10,
      variance = 0.07,
      subdivisions = 2,
      edgeDarken = 0.42,
      granulation = 0.32,
      blur = 0.8,
      composite = 'multiply',
      centerFade = 0.14,
    } = options;

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const p of pts) {
      if (p[0] < minX) minX = p[0];
      if (p[1] < minY) minY = p[1];
      if (p[0] > maxX) maxX = p[0];
      if (p[1] > maxY) maxY = p[1];
    }
    const pad = Math.max(20, Math.hypot(maxX - minX, maxY - minY) * variance * 1.1 + blur * 4);
    const bx = Math.max(0, Math.floor(minX - pad));
    const by = Math.max(0, Math.floor(minY - pad));
    const bw = Math.min(this.w - bx, Math.ceil(maxX - minX + pad * 2));
    const bh = Math.min(this.h - by, Math.ceil(maxY - minY + pad * 2));
    if (bw <= 2 || bh <= 2) return;

    const sctx = this.sctx;
    sctx.save();
    sctx.clearRect(bx, by, bw, bh);
    if (blur > 0) sctx.filter = `blur(${blur}px)`;

    const c1 = hexToRgb(color);
    const c2 = color2 ? hexToRgb(color2) : c1;
    const perLayerAlpha = Math.min(0.45, (alpha / layers) * 1.75);
    const basePoly = variance > 0.01 ? deformPolygon(pts, this.rng, subdivisions, variance * 0.65, true) : pts;

    for (let i = 0; i < layers; i++) {
      const poly = variance > 0.01 ? deformPolygon(basePoly, this.rng, 1, variance * 0.45, true) : basePoly;
      const t = i / Math.max(1, layers - 1);
      const r = c1[0] * (1 - t) + c2[0] * t + this.rng.gauss(0, 3);
      const g = c1[1] * (1 - t) + c2[1] * t + this.rng.gauss(0, 3);
      const b = c1[2] * (1 - t) + c2[2] * t + this.rng.gauss(0, 3);
      traceSmoothPoly(sctx, poly, true);
      sctx.fillStyle = rgbStr(r, g, b, perLayerAlpha);
      sctx.fill();
    }
    sctx.filter = 'none';
    sctx.restore();

    if (edgeDarken > 0 || granulation > 0 || centerFade > 0) {
      const img = sctx.getImageData(bx, by, bw, bh);
      const d = img.data;
      const w = this.w;
      const alphas = new Uint8Array(bw * bh);
      for (let i = 0; i < bw * bh; i++) alphas[i] = d[i * 4 + 3];

      for (let ly = 0; ly < bh; ly++) {
        const gy = by + ly;
        const rowOff = ly * bw;
        for (let lx = 0; lx < bw; lx++) {
          const idx = rowOff + lx;
          const a = alphas[idx];
          if (a < 2) continue;

          const gx = bx + lx;
          const tooth = this.heightMap[gy * w + gx];
          const mottle = this.noise.sample(gx * 0.018, gy * 0.018);

          // Crisp dried-watercolor pigment rim ONLY at true outer boundaries
          let rim = 0;
          if (edgeDarken > 0 && a > 18 && lx >= 3 && lx < bw - 3 && ly >= 3 && ly < bh - 3) {
            const minN = Math.min(
              alphas[idx - 3],
              alphas[idx + 3],
              alphas[idx - bw * 3],
              alphas[idx + bw * 3]
            );
            if (minN < 16) rim = Math.min(1, ((a - minN) / 255) * 1.9);
          }

          const granFactor = 1 + (0.5 - tooth) * granulation * 1.15 + (mottle - 0.5) * 0.28;
          const rimFactor = 1 + rim * edgeDarken * 0.95;
          const centerLift = 1 - centerFade * (1 - rim) * (a / 255) * 0.40;

          const p = idx * 4;
          if (rim > 0.05) {
            const dk = 1 - rim * edgeDarken * 0.14;
            d[p] *= dk;
            d[p + 1] *= dk;
            d[p + 2] *= dk;
          }
          d[p + 3] = Math.max(0, Math.min(255, a * granFactor * rimFactor * centerLift));
        }
      }
      sctx.putImageData(img, bx, by);
    }

    this.ctx.save();
    this.ctx.globalCompositeOperation = composite;
    this.ctx.drawImage(this.scratch, bx, by, bw, bh, bx, by, bw, bh);
    this.ctx.restore();
  }

  // Smooth wet-on-wet atmospheric wash (no edges, no stripes, pure luminous glow)
  bloom(cx, cy, rx, ry, color, alpha = 0.35, composite = 'multiply', rot = 0) {
    const [r, g, b] = hexToRgb(color);
    this.ctx.save();
    this.ctx.globalCompositeOperation = composite;
    this.ctx.translate(cx, cy);
    this.ctx.rotate(rot);
    this.ctx.scale(1, ry / Math.max(1, rx));
    for (let i = 0; i < 3; i++) {
      const ox = this.rng.gauss(0, rx * 0.14);
      const oy = this.rng.gauss(0, rx * 0.14);
      const rad = rx * this.rng.range(0.80, 1.12);
      const grad = this.ctx.createRadialGradient(ox, oy, 0, ox, oy, rad);
      const a = alpha * 0.45;
      grad.addColorStop(0, rgbStr(r, g, b, a));
      grad.addColorStop(0.55, rgbStr(r, g, b, a * 0.52));
      grad.addColorStop(1, rgbStr(r, g, b, 0));
      this.ctx.fillStyle = grad;
      this.ctx.beginPath();
      this.ctx.arc(ox, oy, rad, 0, Math.PI * 2);
      this.ctx.fill();
    }
    this.ctx.restore();
  }

  // Crisp-edged watercolor foliage / petal dab cluster with soft unifying base wash
  foliageDabs(cx, cy, rx, ry, count, colors, options = {}) {
    const {
      dabMin = 12,
      dabMax = 32,
      alpha = 0.52,
      blur = 0.5,
      edgeDarken = 0.40,
    } = options;

    // Soft unifying wet-on-wet undertone so individual leaf dabs read as lush foliage canopy
    this.bloom(cx, cy, rx * 0.92, ry * 0.88, colors[0], alpha * 0.45, 'multiply');

    for (let i = 0; i < count; i++) {
      const ang = this.rng.range(0, Math.PI * 2);
      const dist = Math.sqrt(this.rng.next());
      const x = cx + Math.cos(ang) * rx * dist;
      const y = cy + Math.sin(ang) * ry * dist;
      const drx = this.rng.range(dabMin, dabMax);
      const dry = drx * this.rng.range(0.52, 0.92);
      const rot = this.rng.range(0, Math.PI);
      const col = colors[Math.floor(this.rng.next() * colors.length)];
      this.wash(ellipsePoints(x, y, drx, dry, 10, rot), {
        color: col,
        alpha: alpha * this.rng.range(0.70, 1.05),
        layers: 3,
        variance: 0.14,
        subdivisions: 2,
        edgeDarken,
        granulation: 0.26,
        blur,
        composite: 'multiply',
        centerFade: 0.16,
      });
    }
  }

  // Luminous sunlit glow
  sunHighlight(cx, cy, rx, ry, color = '#FFFDF2', alpha = 0.65, rot = 0, blur = 8) {
    const pts = ellipsePoints(cx, cy, rx, ry, 16, rot);
    this.ctx.save();
    this.ctx.globalCompositeOperation = 'screen';
    if (blur > 0) this.ctx.filter = `blur(${blur}px)`;
    const [r, g, b] = hexToRgb(color);
    const grad = this.ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(rx, ry));
    grad.addColorStop(0, rgbStr(r, g, b, alpha));
    grad.addColorStop(0.6, rgbStr(r, g, b, alpha * 0.45));
    grad.addColorStop(1, rgbStr(r, g, b, 0));
    this.ctx.fillStyle = grad;
    traceSmoothPoly(this.ctx, pts, true);
    this.ctx.fill();
    this.ctx.filter = 'none';
    this.ctx.restore();
  }

  // Reserved clean paper white / gouache highlight
  gouache(pts, color = '#FDFBF5', alpha = 0.92, blur = 0.4) {
    this.ctx.save();
    this.ctx.globalCompositeOperation = 'source-over';
    if (blur > 0) this.ctx.filter = `blur(${blur}px)`;
    const [r, g, b] = hexToRgb(color);
    this.ctx.fillStyle = rgbStr(r, g, b, alpha);
    traceSmoothPoly(this.ctx, pts, true);
    this.ctx.fill();
    this.ctx.filter = 'none';
    this.ctx.restore();
  }

  // Tapered organic watercolor brush stroke (juicy wet-on-dry reed/leaf/water stroke)
  brushStroke(points, options = {}) {
    const {
      color = '#65AC5A',
      width = 8,
      alpha = 0.58,
      taperStart = 0.25,
      taperEnd = 0.04,
      composite = 'multiply',
      blur = 0.4,
      dryness = 0.22,
    } = options;

    if (points.length < 2) return;
    const left = [], right = [];
    for (let i = 0; i < points.length; i++) {
      const t = i / (points.length - 1);
      const p = points[i];
      const prev = points[Math.max(0, i - 1)];
      const next = points[Math.min(points.length - 1, i + 1)];
      const dx = next[0] - prev[0];
      const dy = next[1] - prev[1];
      const len = Math.hypot(dx, dy) || 1;
      const nx = -dy / len;
      const ny = dx / len;

      const bell = Math.sin(t * Math.PI);
      const wFactor = (taperStart * (1 - t) + taperEnd * t) * 0.35 + bell * 0.85;
      const halfW = width * 0.5 * wFactor * (1 + this.rng.gauss(0, 0.05));
      left.push([p[0] + nx * halfW, p[1] + ny * halfW]);
      right.unshift([p[0] - nx * halfW, p[1] - ny * halfW]);
    }
    this.wash([...left, ...right], {
      color,
      alpha,
      layers: 5,
      variance: 0.06,
      subdivisions: 2,
      edgeDarken: 0.36,
      granulation: 0.28 + dryness * 0.45,
      blur,
      composite,
      centerFade: 0.12,
    });
  }

  // Delicate colored-pencil picture-book linework (warm sepia / soft sienna / slate-blue)
  pencil(points, options = {}) {
    const {
      color = '#6E5544',
      width = 1.4,
      alpha = 0.55,
      jitter = 0.55,
      toothBreak = 0.30,
      passes = 2,
    } = options;

    const [r, g, b] = hexToRgb(color);
    this.ctx.save();
    this.ctx.globalCompositeOperation = 'multiply';
    this.ctx.lineCap = 'round';
    this.ctx.lineJoin = 'round';

    for (let pass = 0; pass < passes; pass++) {
      const subPts = [];
      for (let i = 0; i < points.length - 1; i++) {
        const p1 = points[i], p2 = points[i + 1];
        const dist = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
        const steps = Math.max(2, Math.ceil(dist / 3.5));
        for (let s = 0; s < steps; s++) {
          const t = s / steps;
          subPts.push([
            p1[0] + (p2[0] - p1[0]) * t + this.rng.gauss(0, jitter * (pass === 0 ? 0.5 : 0.9)),
            p1[1] + (p2[1] - p1[1]) * t + this.rng.gauss(0, jitter * (pass === 0 ? 0.5 : 0.9)),
          ]);
        }
      }
      subPts.push(points[points.length - 1]);

      for (let i = 0; i < subPts.length - 1; i++) {
        const p1 = subPts[i], p2 = subPts[i + 1];
        const mx = Math.max(0, Math.min(this.w - 1, Math.round((p1[0] + p2[0]) * 0.5)));
        const my = Math.max(0, Math.min(this.h - 1, Math.round((p1[1] + p2[1]) * 0.5)));
        const tooth = this.heightMap[my * this.w + mx];
        const t = i / Math.max(1, subPts.length - 1);
        const endFade = Math.sin(Math.min(1, t * 5) * Math.PI * 0.5) * Math.sin(Math.min(1, (1 - t) * 5) * Math.PI * 0.5);
        const segAlpha = alpha * (pass === 0 ? 0.72 : 0.34) * endFade * (1 - toothBreak * (1 - tooth));
        if (segAlpha < 0.03) continue;

        this.ctx.strokeStyle = rgbStr(r, g, b, segAlpha);
        this.ctx.lineWidth = Math.max(0.5, width * (0.75 + tooth * 0.45) * (pass === 0 ? 1 : 0.75));
        this.ctx.beginPath();
        this.ctx.moveTo(p1[0], p1[1]);
        this.ctx.lineTo(p2[0], p2[1]);
        this.ctx.stroke();
      }
    }
    this.ctx.restore();
  }

  ripple(cx, cy, rx, ry, options = {}) {
    const {
      lightColor = '#FFFDF8',
      shadowColor = '#5697B8',
      alpha = 0.68,
      thickness = 2.1,
    } = options;

    const drawArc = (yOff, color, a, w, comp) => {
      this.ctx.save();
      this.ctx.globalCompositeOperation = comp;
      const [r, g, b] = hexToRgb(color);
      const segs = 44;
      for (let i = 0; i < segs; i++) {
        const a1 = (i / segs) * Math.PI * 2;
        const a2 = ((i + 1) / segs) * Math.PI * 2;
        const gap = Math.sin(a1 * 2 + 0.6) * 0.35 + 0.65;
        if (gap < 0.38) continue;
        const x1 = cx + Math.cos(a1) * rx + this.rng.gauss(0, 0.5);
        const y1 = cy + yOff + Math.sin(a1) * ry + this.rng.gauss(0, 0.3);
        const x2 = cx + Math.cos(a2) * rx + this.rng.gauss(0, 0.5);
        const y2 = cy + yOff + Math.sin(a2) * ry + this.rng.gauss(0, 0.3);
        this.ctx.strokeStyle = rgbStr(r, g, b, a * gap);
        this.ctx.lineWidth = w * (0.65 + 0.5 * Math.abs(Math.sin(a1)));
        this.ctx.lineCap = 'round';
        this.ctx.beginPath();
        this.ctx.moveTo(x1, y1);
        this.ctx.lineTo(x2, y2);
        this.ctx.stroke();
      }
      this.ctx.restore();
    };

    drawArc(2.0, shadowColor, alpha * 0.42, thickness * 1.15, 'multiply');
    drawArc(0, lightColor, alpha * 0.88, thickness, 'source-over');
  }

  splatter(cx, cy, radius, count, color, alpha = 0.42) {
    const [r, g, b] = hexToRgb(color);
    this.ctx.save();
    this.ctx.globalCompositeOperation = 'multiply';
    for (let i = 0; i < count; i++) {
      const ang = this.rng.range(0, Math.PI * 2);
      const dist = Math.pow(this.rng.next(), 0.72) * radius;
      const x = cx + Math.cos(ang) * dist;
      const y = cy + Math.sin(ang) * dist;
      const rad = this.rng.range(1.0, 3.6);
      this.ctx.fillStyle = rgbStr(r, g, b, alpha * this.rng.range(0.45, 1.0));
      this.ctx.beginPath();
      this.ctx.ellipse(x, y, rad, rad * this.rng.range(0.75, 1.25), this.rng.range(0, Math.PI), 0, Math.PI * 2);
      this.ctx.fill();
    }
    this.ctx.restore();
  }

  finishPictureBook(warmth = 0.08, marginFade = true) {
    // Subtle paper tooth unification across highlights
    this.ctx.save();
    this.ctx.globalCompositeOperation = 'multiply';
    this.ctx.globalAlpha = 0.16;
    this.ctx.drawImage(this.paperCanvas, 0, 0);
    this.ctx.restore();

    if (warmth > 0) {
      this.ctx.save();
      this.ctx.globalCompositeOperation = 'soft-light';
      this.ctx.fillStyle = `rgba(255, 242, 208, ${warmth})`;
      this.ctx.fillRect(0, 0, this.w, this.h);
      this.ctx.restore();
    }

    if (marginFade) {
      this.ctx.save();
      const grad = this.ctx.createRadialGradient(
        this.w * 0.5, this.h * 0.5, Math.min(this.w, this.h) * 0.45,
        this.w * 0.5, this.h * 0.5, Math.hypot(this.w, this.h) * 0.57
      );
      grad.addColorStop(0, 'rgba(253,250,242,0)');
      grad.addColorStop(0.82, 'rgba(253,250,242,0.10)');
      grad.addColorStop(1, 'rgba(253,250,242,0.75)');
      this.ctx.fillStyle = grad;
      this.ctx.fillRect(0, 0, this.w, this.h);
      this.ctx.restore();
    }
  }
}
