// animate_scenes.js
// 30-second animated watercolor picture-book film engine for 《纸船的故事》
// Zero-flicker cached watercolor backgrounds + live animated rippled reflections +
// expressive character animation + smooth camera moves + optical Arches paper finishing!

import { WatercolorStudio, ellipsePts, sampleBezierShape, sampleCubic, rgba } from './watercolor_v2.js';
import {
  PAL,
  drawPaperBoat,
  drawFluffyDuckling,
  drawRiverStone,
  drawFloatingLeaf,
  drawReedCluster,
  drawWillowBranch,
  drawWildflower,
} from './characters_v2.js';

// Smooth easing helpers
const clamp01 = (v) => Math.max(0, Math.min(1, v));
const smoothstep = (a, b, x) => {
  const t = clamp01((x - a) / (b - a));
  return t * t * (3 - 2 * t);
};
const easeOutCubic = (t) => 1 - Math.pow(1 - clamp01(t), 3);
const easeInOutSine = (t) => -(Math.cos(Math.PI * clamp01(t)) - 1) / 2;
const lerp = (a, b, t) => a + (b - a) * t;

function xform(pts, cx, cy, scale, rot = 0, flipX = false) {
  const cos = Math.cos(rot), sin = Math.sin(rot), fx = flipX ? -1 : 1;
  return pts.map(([x, y]) => {
    const sx = x * scale * fx, sy = y * scale;
    return [cx + sx * cos - sy * sin, cy + sx * sin + sy * cos];
  });
}

// Animated version of our beloved straw-hat storybook child (animated arm, ribbon, blink, head gaze!)
function drawAnimatedChild(st, cx, cy, scale, anim = {}) {
  const {
    armLift = 0,       // negative = holding boat up, 0 = touching water, positive = gently retracted
    headTilt = 0.25,   // downward gaze angle
    ribbonPhase = 0,   // breeze flutter phase
    blink = 0,         // 0 = open happy curve, 1 = gentle full blink
  } = anim;

  const T = (pts) => xform(pts, cx, cy, scale, 0, false);

  st.glow(cx - 8 * scale, cy + 162 * scale, 124 * scale, 28 * scale, '#3E7858', 0.40, 'multiply');

  // Far leg & shoe
  const farCalf = T(sampleBezierShape([
    [[34, 82], [50, 88], [56, 114], [48, 142]],
    [[48, 142], [38, 148], [26, 146], [22, 136]],
    [[22, 136], [20, 112], [22, 88], [34, 82]],
  ], 8));
  st.reserve(farCalf, '#FAECE0', 0.94);
  st.wash(farCalf, { color: PAL.skinShade, alpha: 0.64, layers: 4, rimStroke: 0.16 });

  const farShoe = T(sampleBezierShape([
    [[22, 138], [42, 138], [64, 143], [72, 152]],
    [[72, 152], [72, 160], [52, 163], [26, 161]],
    [[26, 161], [18, 158], [16, 146], [22, 138]],
  ], 8));
  st.reserve(farShoe, '#F5E2D4', 0.94);
  st.wash(farShoe, { color: '#B56350', color2: '#8C4838', alpha: 0.84, layers: 5, rimStroke: 0.24 });

  // Front squatting leg
  const shorts = T(sampleBezierShape([
    [[-64, 62], [-22, 42], [20, 38], [40, 56]],
    [[40, 56], [48, 72], [38, 92], [18, 100]],
    [[18, 100], [-14, 112], [-54, 118], [-74, 102]],
    [[-74, 102], [-84, 86], [-78, 68], [-64, 62]],
  ], 10));
  st.reserve(shorts, '#FCF8EE', 0.96);
  st.wash(shorts, { color: PAL.shortsLight, color2: PAL.shortsShade, alpha: 0.82, layers: 5, rimStroke: 0.24 });

  const frontLeg = T(sampleBezierShape([
    [[22, 64], [38, 66], [42, 82], [28, 106]],
    [[28, 106], [16, 126], [4, 142], [-10, 146]],
    [[-10, 146], [-24, 144], [-26, 132], [-16, 114]],
    [[-16, 114], [-4, 92], [8, 72], [22, 64]],
  ], 10));
  st.reserve(frontLeg, '#FFF5EC', 0.96);
  st.wash(frontLeg, { color: PAL.skinLight, color2: PAL.skinShade, alpha: 0.70, layers: 4, rimStroke: 0.18 });

  const sock = T(sampleBezierShape([
    [[-20, 130], [-4, 128], [4, 138], [2, 150]],
    [[2, 150], [-10, 154], [-24, 150], [-24, 138]],
    [[-24, 138], [-23, 133], [-21, 131], [-20, 130]],
  ], 6));
  st.reserve(sock, '#FFFDF8', 0.97);
  st.wash(sock, { color: '#E8E0D2', alpha: 0.32, layers: 3, rimStroke: 0.16 });

  const frontShoe = T(sampleBezierShape([
    [[-26, 144], [-6, 144], [18, 148], [28, 157]],
    [[28, 157], [28, 166], [6, 169], [-20, 167]],
    [[-20, 167], [-32, 163], [-32, 150], [-26, 144]],
  ], 8));
  st.reserve(frontShoe, '#FCEBE0', 0.96);
  st.wash(frontShoe, { color: PAL.shoe, color2: PAL.shoeDeep, alpha: 0.88, layers: 5, rimStroke: 0.26 });

  // Sky-blue linen smock
  const tunic = T(sampleBezierShape([
    [[-10, -50], [14, -50], [34, -36], [40, -10]],
    [[40, -10], [42, 18], [30, 52], [6, 74]],
    [[6, 74], [-26, 86], [-64, 88], [-84, 70]],
    [[-84, 70], [-94, 40], [-78, -4], [-42, -36]],
    [[-42, -36], [-28, -46], [-16, -50], [-10, -50]],
  ], 10));
  st.reserve(tunic, '#F6FAFE', 0.97);
  st.wash(tunic, { color: PAL.tunicLight, color2: PAL.tunicMid, alpha: 0.82, layers: 6, variance: 0.03, rimStroke: 0.26 });
  st.glow(cx - 56 * scale, cy + 48 * scale, 40 * scale, 34 * scale, PAL.tunicShade, 0.38, 'multiply', -0.2);
  st.glow(cx + 22 * scale, cy - 16 * scale, 22 * scale, 28 * scale, '#FFFDF4', 0.36, 'screen');

  // Neck + Peter Pan collar
  const neck = T([[-6, -78], [22, -72], [24, -36], [-8, -38]]);
  st.reserve(neck, '#FCE9D8', 0.95);
  st.wash(neck, { color: PAL.skinShade, alpha: 0.44, layers: 3, rimStroke: 0 });

  const collar = T(sampleBezierShape([
    [[-18, -50], [6, -46], [26, -38], [34, -28]],
    [[34, -28], [20, -20], [-2, -22], [-24, -32]],
    [[-24, -32], [-28, -40], [-24, -48], [-18, -50]],
  ], 8));
  st.reserve(collar, '#FFFDF7', 0.98);
  st.wash(collar, { color: '#F2E7D2', alpha: 0.38, layers: 3, rimStroke: 0.22 });

  // Sleeve
  const sleeve = T(sampleBezierShape([
    [[-22, -26], [-2, -30], [16, -18], [22, 6]],
    [[22, 6], [22, 22], [8, 28], [-10, 24]],
    [[-10, 24], [-24, 14], [-30, -2], [-26, -18]],
    [[-26, -18], [-25, -23], [-24, -25], [-22, -26]],
  ], 8));
  st.reserve(sleeve, '#F6FAFE', 0.97);
  st.wash(sleeve, { color: PAL.tunicLight, color2: PAL.tunicMid, alpha: 0.80, layers: 5, rimStroke: 0.24 });

  // Animated bent reaching arm (rotates gently around shoulder/elbow pivot!)
  const TA = (pts) => {
    const aRot = armLift * 0.16;
    const cos = Math.cos(aRot), sin = Math.sin(aRot);
    return pts.map(([x, y]) => {
      const rx = x - 6, ry = y - 14;
      return [cx + (6 + rx * cos - ry * sin) * scale, cy + (14 + rx * sin + ry * cos) * scale];
    });
  };
  const armAndHand = TA(sampleBezierShape([
    [[14, 14], [22, 28], [28, 40], [34, 46]],
    [[34, 46], [56, 62], [78, 74], [98, 82]],
    [[98, 82], [112, 80], [124, 83], [128, 89]],
    [[128, 89], [124, 93], [118, 93], [136, 97]],
    [[136, 97], [142, 102], [136, 107], [126, 107]],
    [[126, 107], [112, 109], [96, 104], [84, 96]],
    [[84, 96], [54, 80], [24, 66], [8, 52]],
    [[8, 52], [-4, 40], [-6, 26], [-4, 16]],
    [[-4, 16], [2, 12], [8, 12], [14, 14]],
  ], 8));
  st.reserve(armAndHand, '#FFF6EE', 0.97);
  st.wash(armAndHand, { color: PAL.skinLight, color2: PAL.skinShade, alpha: 0.70, layers: 4, rimStroke: 0.18 });

  // Tilted Head + Sunlit Straw Hat with fluttering coral ribbon!
  const TH = (pts) => {
    const cos = Math.cos(headTilt), sin = Math.sin(headTilt);
    return pts.map(([x, y]) => {
      const rx = x - 14, ry = y + 58;
      return [cx + (14 + rx * cos - ry * sin) * scale, cy + (-58 + rx * sin + ry * cos) * scale];
    });
  };

  const hatBackBrim = TH(ellipsePts(10, -124, 72, 24, 20, -0.06));
  st.reserve(hatBackBrim, '#F9E7B6', 0.92);
  st.wash(hatBackBrim, { color: PAL.hatMid, color2: PAL.hatShade, alpha: 0.78, layers: 4, rimStroke: 0.26 });

  const face = TH(sampleBezierShape([
    [[-8, -132], [22, -134], [46, -118], [52, -100]],
    [[52, -100], [56, -92], [60, -87], [55, -82]],
    [[55, -82], [53, -72], [44, -60], [28, -52]],
    [[28, -52], [8, -48], [-14, -64], [-22, -92]],
    [[-22, -92], [-24, -114], [-18, -128], [-8, -132]],
  ], 10));
  st.reserve(face, '#FFF8F1', 0.98);
  st.wash(face, { color: PAL.skinLight, color2: PAL.skinShade, alpha: 0.58, layers: 5, rimStroke: 0.14 });
  const shPt = TH([[26, -114]])[0];
  st.glow(shPt[0], shPt[1], 32 * scale, 12 * scale, '#9AA8C4', 0.28, 'multiply', 0.15);

  const ckPt = TH([[34, -77]])[0];
  st.glow(ckPt[0], ckPt[1], 14 * scale, 10 * scale, PAL.cheek, 0.48, 'multiply');

  // Gentle downward-looking happy eye (with warm blink!)
  const eyePt = TH([[41, -93]])[0];
  st.ctx.save();
  st.ctx.strokeStyle = '#4A2B1D';
  st.ctx.lineWidth = (2.4 + blink * 0.5) * scale;
  st.ctx.lineCap = 'round';
  st.ctx.beginPath();
  if (blink > 0.5) {
    st.ctx.moveTo(eyePt[0] - 4.5 * scale, eyePt[1]);
    st.ctx.quadraticCurveTo(eyePt[0], eyePt[1] + 2.5 * scale, eyePt[0] + 4.5 * scale, eyePt[1]);
  } else {
    st.ctx.arc(eyePt[0], eyePt[1] - 1.5 * scale, 4.8 * scale, 0.18 * Math.PI, 0.88 * Math.PI);
  }
  st.ctx.stroke();
  st.ctx.restore();
  st.pencil(TH([[43, -69], [49, -68], [54, -72]]), { color: '#C4685E', width: 1.35 * scale, alpha: 0.72, passes: 1 });

  const hairUnder = TH(sampleBezierShape([
    [[-34, -116], [-10, -124], [24, -122], [46, -112]],
    [[46, -112], [32, -108], [16, -110], [4, -92]],
    [[4, -92], [-2, -74], [-14, -56], [-32, -62]],
    [[-32, -62], [-42, -78], [-42, -100], [-34, -116]],
  ], 10));
  st.reserve(hairUnder, '#EBD6C0', 0.90);
  st.wash(hairUnder, { color: PAL.hairMid, color2: PAL.hairDeep, alpha: 0.86, layers: 5, variance: 0.04, rimStroke: 0.24 });

  const ear = TH(ellipsePts(1, -86, 6.6, 8.4, 10));
  st.reserve(ear, '#FFE4CE', 0.95);
  st.wash(ear, { color: PAL.skinShade, alpha: 0.40, layers: 3, rimStroke: 0 });

  // Sunlit straw sunhat
  const hatCrown = TH(sampleBezierShape([
    [[-44, -128], [-40, -168], [-8, -184], [24, -180]],
    [[24, -180], [50, -172], [58, -148], [52, -124]],
    [[52, -124], [24, -116], [-18, -118], [-44, -128]],
  ], 10));
  const hatFrontBrim = TH(sampleBezierShape([
    [[-64, -122], [-34, -136], [28, -138], [82, -118]],
    [[82, -118], [86, -108], [56, -102], [10, -108]],
    [[10, -108], [-38, -112], [-68, -112], [-64, -122]],
  ], 10));
  st.reserve(hatCrown, '#FFF8E2', 0.96);
  st.wash(hatCrown, { color: PAL.hatLight, color2: PAL.hatMid, alpha: 0.86, layers: 5, variance: 0.04, rimStroke: 0.28 });
  st.reserve(hatFrontBrim, '#FFF9E8', 0.96);
  st.wash(hatFrontBrim, { color: PAL.hatLight, color2: PAL.hatMid, alpha: 0.80, layers: 5, variance: 0.04, rimStroke: 0.26 });
  const hlHat = TH([[26, -162]])[0];
  st.glow(hlHat[0], hlHat[1], 30 * scale, 16 * scale, '#FFFDF5', 0.60, 'screen', 0.25);

  // Coral ribbon & gently fluttering ribbon tails!
  const fl1 = Math.sin(ribbonPhase) * 6;
  const fl2 = Math.cos(ribbonPhase * 1.2 + 0.8) * 5;
  st.stroke(TH([[-44, -132], [-8, -124], [26, -124], [52, -128]]), { color: PAL.ribbon, width: 10 * scale, alpha: 0.88, rimStroke: 0.20 });
  st.wash(TH(ellipsePts(-50, -134, 14, 7, 10, -0.4 + fl1 * 0.015)), { color: PAL.ribbon, color2: PAL.ribbonDeep, alpha: 0.88, layers: 3, rimStroke: 0.22 });
  st.wash(TH(ellipsePts(-54, -122, 13, 6.5, 10, 0.45 + fl2 * 0.015)), { color: PAL.ribbon, color2: PAL.ribbonDeep, alpha: 0.88, layers: 3, rimStroke: 0.22 });
  st.stroke(TH([[-48, -128], [-68 + fl1 * 0.5, -104], [-78 + fl1, -82]]), { color: PAL.ribbon, width: 7 * scale, alpha: 0.84 });
  st.stroke(TH([[-46, -126], [-58 + fl2 * 0.5, -98], [-62 + fl2, -76]]), { color: PAL.ribbonDeep, width: 6 * scale, alpha: 0.78 });

  // Clean pencil accents
  const lp = { color: PAL.sepia, width: 1.3 * scale, alpha: 0.44, jitter: 0.22 * scale, passes: 1 };
  const bp = { color: PAL.indigo, width: 1.3 * scale, alpha: 0.42, jitter: 0.22 * scale, passes: 1 };
  st.pencil(TH(sampleCubic([50, -104], [56, -92], [60, -87], [55, -82], 8)), lp);
  st.pencil(TH(sampleCubic([55, -82], [52, -72], [44, -58], [24, -50], 8)), lp);
  st.pencil(TH(sampleCubic([-64, -122], [-18, -112], [42, -106], [82, -118], 10)), { color: '#9E7336', width: 1.2 * scale, alpha: 0.46, jitter: 0.2, passes: 1 });
  st.pencil(T(sampleCubic([-42, -36], [-78, -4], [-94, 40], [-84, 70], 10)), bp);
  st.pencil(T(sampleCubic([-84, 70], [-64, 88], [-22, 86], [10, 72], 10)), bp);
  st.pencil(TA(sampleCubic([14, 14], [22, 32], [28, 42], [34, 46], 6)), lp);
  st.pencil(TA(sampleCubic([34, 46], [56, 62], [78, 74], [98, 82], 8)), lp);
  st.pencil(TA(sampleCubic([136, 106], [100, 108], [46, 78], [8, 52], 10)), { ...lp, alpha: 0.36 });
  st.pencil(T(sampleCubic([36, 68], [42, 84], [22, 118], [2, 142], 10)), lp);
}

// ============================================================================
// FILM DIRECTOR: Caches each shot's painted upper landscape & paper LUT ONCE,
// then renders live animated water reflections, swaying willows, ripples & characters!
// ============================================================================
export class PaperBoatFilm {
  constructor(width = 1600, height = 900) {
    this.w = width;
    this.h = height;

    // Precompute cold-press Arches 300gsm paper tooth & domain-warp LUT ONCE (massive speedup & zero flicker!)
    this.paperMod = new Float32Array(width * height);
    this.granMod = new Float32Array(width * height);
    this.warpIdx = new Int32Array(width * height);
    this._precomputePaperLUT();

    // Scratch buffers for two-shot cross-dissolve & final compositing
    this.bufA = document.createElement('canvas');
    this.bufA.width = width;
    this.bufA.height = height;
    this.bufB = document.createElement('canvas');
    this.bufB.width = width;
    this.bufB.height = height;

    this.shots = {};
    this._buildShotCaches();
  }

  _precomputePaperLUT() {
    const w = this.w, h = this.h;
    const dummy = document.createElement('canvas');
    dummy.width = 4; dummy.height = 4;
    const st = new WatercolorStudio(dummy, 2026);
    const warp = 1.25;
    for (let y = 0; y < h; y++) {
      const row = y * w;
      for (let x = 0; x < w; x++) {
        const dimple = st.noise1.fbm(x * 0.085, y * 0.085, 3);
        const fine = st.noise2.sample(x * 0.34, y * 0.34);
        const tooth = dimple * 0.65 + fine * 0.35;
        this.paperMod[row + x] = 1.0 + (tooth - 0.5) * 0.09;
        this.granMod[row + x] = (0.5 - tooth) * 0.19;
        const wx = (st.noise1.sample(x * 0.045, y * 0.045) - 0.5) * 2.0 * warp;
        const wy = (st.noise2.sample(x * 0.045 + 31.7, y * 0.045 + 17.3) - 0.5) * 2.0 * warp;
        const sx = Math.max(0, Math.min(w - 1, Math.round(x + wx)));
        const sy = Math.max(0, Math.min(h - 1, Math.round(y + wy)));
        this.warpIdx[row + x] = (sy * w + sx) * 4;
      }
    }
  }

  _applyFastPaperPhysics(canvas, warmth = 0.06) {
    const w = this.w, h = this.h;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    const srcImg = ctx.getImageData(0, 0, w, h);
    const src = srcImg.data;
    const dstImg = ctx.createImageData(w, h);
    const dst = dstImg.data;
    const pMod = this.paperMod, gMod = this.granMod, wIdx = this.warpIdx;
    const n = w * h;

    for (let i = 0; i < n; i++) {
      const sp = wIdx[i];
      const r0 = src[sp], g0 = src[sp + 1], b0 = src[sp + 2];
      const lum = (r0 * 0.299 + g0 * 0.587 + b0 * 0.114) * 0.00392157;
      const mod = pMod[i] * (1.0 - gMod[i] * (1.0 - lum));
      const dp = i * 4;
      dst[dp] = r0 * mod > 255 ? 255 : r0 * mod;
      dst[dp + 1] = g0 * mod * 0.998 > 255 ? 255 : g0 * mod * 0.998;
      dst[dp + 2] = b0 * mod * 0.992 > 255 ? 255 : b0 * mod * 0.992;
      dst[dp + 3] = 255;
    }
    ctx.putImageData(dstImg, 0, 0);

    if (warmth > 0) {
      ctx.save();
      ctx.globalCompositeOperation = 'soft-light';
      ctx.fillStyle = `rgba(255, 240, 200, ${warmth})`;
      ctx.fillRect(0, 0, w, h);
      ctx.restore();
    }
    // Storybook deckle margin vignette
    ctx.save();
    const grad = ctx.createRadialGradient(w * 0.5, h * 0.5, Math.min(w, h) * 0.45, w * 0.5, h * 0.5, Math.hypot(w, h) * 0.58);
    grad.addColorStop(0, 'rgba(252,249,241,0)');
    grad.addColorStop(0.84, 'rgba(252,249,241,0.10)');
    grad.addColorStop(1, 'rgba(252,249,241,0.70)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);
    ctx.restore();
  }

  _buildShotCaches() {
    // Shot 1 upper sky/trees + left meadow bank cache
    this.shots.s1 = this._cacheShot1();
    this.shots.s2 = this._cacheShot2();
    this.shots.s3 = this._cacheShot3();
    this.shots.s4 = this._cacheShot4();
  }

  _makeCanvas() {
    const c = document.createElement('canvas');
    c.width = this.w; c.height = this.h;
    return c;
  }

  _cacheShot1() {
    const skyC = this._makeCanvas();
    const st = new WatercolorStudio(skyC, 5011);
    const horizonY = 335;
    st.paintSky(horizonY, { topColor: '#86C7E8', midColor: '#C8EAF6', horizonColor: '#FFF3C4', sunX: 1290, sunY: 115, sunColor: '#FFE082', cloudCount: 4 });
    st.paintDistantHills(horizonY, [
      { color: '#9CC6C2', color2: '#89B5C4', alpha: 0.42, amp: 58, yOff: -12, freq: 0.0024, phase: 0.5 },
      { color: '#8EC47E', color2: '#6DAA6E', alpha: 0.58, amp: 36, yOff: 2, freq: 0.0038, phase: 2.1 },
    ]);
    st.paintTree(1060, horizonY + 8, 1.02, { sunFromRight: true, alpha: 0.78, lean: -18 });
    st.paintTree(1380, horizonY + 10, 1.24, { sunFromRight: true, alpha: 0.82, lean: 22 });
    st.paintTree(795, horizonY + 5, 0.76, { sunFromRight: true, alpha: 0.62, lean: 14 });
    st.paintTree(235, horizonY + 6, 0.92, { sunFromRight: true, alpha: 0.72, lean: -12 });

    // Pre-paint static left wildflower meadow bank on transparent layer
    const bankC = this._makeCanvas();
    const bst = new WatercolorStudio(bankC, 5019);
    bst.ctx.clearRect(0, 0, this.w, this.h);
    const bankPts = [[-40, 310], [290, 322], [560, 370], [678, 455], [642, 595], [510, 750], [345, 920], [-40, 920]];
    bst.reserve(bankPts, '#FCF9EE', 0.98);
    bst.wash(bankPts, { color: '#A5D462', color2: '#63AB56', alpha: 0.76, layers: 7, variance: 0.06, rimStroke: 0.26 });
    bst.glow(380, 440, 260, 140, '#E8E46E', 0.40, 'multiply');
    bst.glow(160, 680, 240, 160, '#4E8F5C', 0.28, 'multiply');
    for (let i = 0; i < 30; i++) {
      const gx = bst.rng.range(30, 610), gy = bst.rng.range(360, 880);
      if (gx + (gy - 360) * 0.44 > 700) continue;
      bst.paintGrassTuft(gx, gy, bst.rng.range(5, 9), bst.rng.range(30, 66), { lean: 0.16, alpha: 0.66, width: 4.2 });
    }
    bst.paintGrassTuft(655, 455, 8, 52, { lean: 0.35, alpha: 0.72, width: 4.5 });
    bst.paintGrassTuft(632, 575, 7, 46, { lean: 0.32, alpha: 0.68, width: 4.2 });
    bst.paintGrassTuft(520, 725, 8, 54, { lean: 0.28, alpha: 0.68, width: 4.5 });
    bst.paintGrassTuft(410, 835, 9, 60, { lean: 0.24, alpha: 0.70, width: 4.8 });
    drawRiverStone(bst, 610, 495, 46, 24, { rot: 0.14, moss: true, inWater: false });
    drawRiverStone(bst, 550, 635, 58, 26, { rot: -0.08, moss: true, inWater: false });
    const flowers = [
      [145, 560, 1.2, '#FFFFFF', '#FFC53D'], [195, 612, 1.0, '#FFE47A', '#E88E38'],
      [110, 660, 1.05, '#A6D2FF', '#FFE066'], [265, 745, 1.2, '#FFFFFF', '#FFC53D'],
      [455, 540, 0.95, '#FFD1CC', '#FFE066'], [355, 705, 1.0, '#A6D2FF', '#FFE066'],
      [225, 485, 0.95, '#FFFFFF', '#FFC53D'], [88, 760, 1.15, '#FFE47A', '#E88E38'],
    ];
    for (const [fx, fy, fs, fc, cc] of flowers) drawWildflower(bst, fx, fy, fs, fc, cc);

    return { skyC, bankC, horizonY };
  }

  _cacheShot2() {
    const skyC = this._makeCanvas();
    const st = new WatercolorStudio(skyC, 5022);
    const horizonY = 275;
    st.paintSky(horizonY, { topColor: '#82BFE0', midColor: '#C2E4F0', horizonColor: '#FFF0C2', sunX: 1420, sunY: 145, sunColor: '#FFE080', cloudCount: 2 });
    st.paintDistantHills(horizonY, [
      { color: '#82B6B0', color2: '#6CA2AE', alpha: 0.48, amp: 52, yOff: -8, freq: 0.0026, phase: 1.2 },
      { color: '#5E9E6E', color2: '#468462', alpha: 0.65, amp: 38, yOff: 4, freq: 0.0036, phase: 2.8 },
    ]);
    st.paintTree(240, horizonY + 12, 1.35, { sunFromRight: true, alpha: 0.86, shadowCol: '#2F6E5C', midCol: '#4F965E', lean: 14 });
    st.paintTree(660, horizonY + 10, 1.15, { sunFromRight: true, alpha: 0.78, shadowCol: '#367560', midCol: '#5BA262', lean: -16 });
    st.paintTree(1020, horizonY + 6, 0.85, { sunFromRight: true, alpha: 0.56, lean: 10 });
    return { skyC, horizonY };
  }

  _cacheShot3() {
    const skyC = this._makeCanvas();
    const st = new WatercolorStudio(skyC, 5033);
    const horizonY = 290;
    st.paintSky(horizonY, { topColor: '#88C9E6', midColor: '#CCEBF6', horizonColor: '#FFEBB8', sunX: 1320, sunY: 115, sunColor: '#FFD670', cloudCount: 3 });
    st.paintDistantHills(horizonY, [
      { color: '#96C4BC', color2: '#82B2BF', alpha: 0.42, amp: 48, yOff: -6, freq: 0.0025, phase: 0.8 },
      { color: '#78B674', color2: '#5B9D68', alpha: 0.56, amp: 32, yOff: 4, freq: 0.0038, phase: 2.0 },
    ]);
    st.paintTree(210, horizonY + 10, 1.18, { sunFromRight: true, alpha: 0.80, lean: -14 });
    st.paintTree(520, horizonY + 6, 0.88, { sunFromRight: true, alpha: 0.62, lean: 16 });
    return { skyC, horizonY };
  }

  _cacheShot4() {
    const skyC = this._makeCanvas();
    const st = new WatercolorStudio(skyC, 5044);
    const horizonY = 330;
    st.paintSky(horizonY, { topColor: '#98D0E8', midColor: '#FDE8B6', horizonColor: '#FFD6A2', sunX: 1185, sunY: 185, sunColor: '#FFCE68', cloudCount: 3 });
    st.glow(1340, 160, 360, 220, '#FFB085', 0.34, 'multiply');
    st.paintDistantHills(horizonY, [
      { color: '#A5C6B8', color2: '#B8B8C8', alpha: 0.38, amp: 52, yOff: -10, freq: 0.0022, phase: 0.4 },
      { color: '#8CC07E', color2: '#B8C87A', alpha: 0.48, amp: 28, yOff: 2, freq: 0.0034, phase: 1.9 },
    ]);
    st.paintTree(180, horizonY + 8, 1.15, { sunFromRight: true, alpha: 0.72, lean: -12 });
    st.paintTree(465, horizonY + 5, 0.78, { sunFromRight: true, alpha: 0.52, lean: 15 });
    st.paintTree(1495, horizonY + 6, 0.90, { sunFromRight: true, alpha: 0.56, midCol: '#9CC468', lightCol: '#E8DC72', lean: -16 });
    return { skyC, horizonY };
  }

  // Live animated silky mirror-reflection stream (zero scanlines, continuous gentle ripple motion!)
  _drawLiveWater(st, skyC, horizonY, timeSec, opts) {
    const { tintTop, tintDeep, shadeTint, sunX, sunWidth, sunColor, reflectionAlpha = 0.44, rippleAmp = 12 } = opts;
    const w = this.w, h = this.h, waterH = h - horizonY;
    const ctx = st.ctx;

    // 1. Copy cached upper landscape
    ctx.drawImage(skyC, 0, 0, w, horizonY, 0, 0, w, horizonY);

    // 2. Build live animated silky reflection on offscreen canvas
    if (!this._reflC) {
      this._reflC = document.createElement('canvas');
      this._reflC.width = w;
    }
    this._reflC.height = waterH;
    const rctx = this._reflC.getContext('2d');
    rctx.clearRect(0, 0, w, waterH);
    const sliceH = 3;
    const phase = timeSec * 2.1;
    for (let y = 0; y < waterH; y += sliceH) {
      const t = y / waterH;
      const srcY = Math.max(0, Math.min(horizonY - sliceH, horizonY - 2 - Math.floor(y * 0.72)));
      const wave = Math.sin(y * 0.065 - phase + t * 5.0) * (rippleAmp * (0.22 + t * 0.92))
                 + Math.sin(y * 0.16 + phase * 1.4) * (rippleAmp * 0.22);
      rctx.drawImage(skyC, 0, srcY, w, sliceH, wave, y, w, sliceH);
    }
    rctx.save();
    rctx.globalCompositeOperation = 'destination-in';
    const fadeG = rctx.createLinearGradient(0, 0, 0, waterH);
    fadeG.addColorStop(0, `rgba(255,255,255,${reflectionAlpha * 0.85})`);
    fadeG.addColorStop(0.45, `rgba(255,255,255,${reflectionAlpha})`);
    fadeG.addColorStop(1, `rgba(255,255,255,${reflectionAlpha * 0.42})`);
    rctx.fillStyle = fadeG;
    rctx.fillRect(0, 0, w, waterH);
    rctx.restore();

    // 3. Base turquoise-cerulean water wash + silky reflection
    ctx.save();
    ctx.fillStyle = '#FCF9F1';
    ctx.fillRect(0, horizonY, w, waterH);
    const baseGrad = ctx.createLinearGradient(0, horizonY, 0, h);
    baseGrad.addColorStop(0, rgba(tintTop, 0.46));
    baseGrad.addColorStop(0.55, rgba(tintDeep, 0.44));
    baseGrad.addColorStop(1, rgba(shadeTint, 0.52));
    ctx.globalCompositeOperation = 'multiply';
    ctx.fillStyle = baseGrad;
    ctx.fillRect(0, horizonY, w, waterH);
    ctx.drawImage(this._reflC, 0, horizonY);
    ctx.restore();

    // 4. Gently drifting current ribbons
    for (let i = 0; i < 12; i++) {
      const u = (i + 0.35) / 12;
      const y = horizonY + 24 + u * (waterH - 42);
      const drift = (timeSec * (28 + (i % 4) * 9) + i * 210) % (w + 520) - 260;
      const len = 320 + (i % 3) * 110;
      st.stroke([
        [drift, y],
        [drift + len * 0.33, y + Math.sin(i + timeSec) * 6],
        [drift + len * 0.66, y - Math.sin(i + timeSec * 0.9) * 6],
        [drift + len, y],
      ], { color: i % 3 === 0 ? shadeTint : tintDeep, width: 12 + u * 12, alpha: 0.16, rimStroke: 0 });
    }

    // 5. Sunlit golden water shimmer & animated twinkling sparkles!
    st.glow(sunX, horizonY + waterH * 0.38, sunWidth, waterH * 0.46, sunColor, 0.44, 'multiply', -0.05);
    st.glow(sunX, horizonY + waterH * 0.32, sunWidth * 0.80, waterH * 0.38, '#FFFDF4', 0.64, 'screen', -0.05);

    for (let i = 0; i < 52; i++) {
      const seed = i * 97.13;
      const u = (Math.sin(seed) * 0.5 + 0.5);
      const y = horizonY + 14 + Math.pow(u, 0.85) * (waterH - 32);
      const spread = sunWidth * (0.32 + u * 0.88);
      const x = sunX + Math.sin(seed * 1.7) * spread * 0.65 + Math.sin(timeSec * 0.9 + i) * 8;
      const twinkle = 0.45 + 0.55 * Math.sin(timeSec * (2.2 + (i % 5) * 0.5) + i * 1.9);
      if (twinkle < 0.18) continue;
      const rx = (5 + (i % 7) * 2.4) * (0.45 + u * 0.80) * (0.7 + twinkle * 0.4);
      const ry = Math.max(1.2, rx * 0.22);
      st.reserve(ellipsePts(x, y, rx, ry, 8), '#FFFFFF', 0.35 + twinkle * 0.55);
    }

    // Soft sunlit shoreline mist
    st.glow(w * 0.5, horizonY + 2, w * 0.65, 26, '#FFFDF5', 0.46, 'screen');
  }

  // Apply gentle camera zoom & pan (smooth Ken Burns feel!)
  _applyCamera(ctx, zoom, panX, panY, drawFn) {
    ctx.save();
    ctx.translate(this.w * 0.5 + panX, this.h * 0.5 + panY);
    ctx.scale(zoom, zoom);
    ctx.translate(-this.w * 0.5, -this.h * 0.5);
    drawFn();
    ctx.restore();
  }

  // ---- SHOT 1: 入水与启程 (0.0s – 7.5s) ----
  _renderShot1(targetCanvas, tLocal, tGlobal) {
    const st = new WatercolorStudio(targetCanvas, 1001);
    const { skyC, bankC, horizonY } = this.shots.s1;
    const p = clamp01(tLocal / 7.5);
    const zoom = lerp(1.14, 1.00, easeInOutSine(p));
    const panX = lerp(90, -15, easeInOutSine(p));
    const panY = lerp(-45, 0, easeInOutSine(p));

    this._applyCamera(st.ctx, zoom, panX, panY, () => {
      this._drawLiveWater(st, skyC, horizonY, tGlobal, {
        tintTop: '#9CE0E2', tintDeep: '#55ABC9', shadeTint: '#4D8BB8',
        sunX: 1280, sunWidth: 360, sunColor: '#FFD96B', reflectionAlpha: 0.44, rippleAmp: 11,
      });
      // Static left wildflower bank
      st.ctx.drawImage(bankC, 0, 0);

      // Child animation: gently lowers boat (0..2.1s), releases at 2.1s, retracts slightly, blinks at 3.8s
      const lowerT = smoothstep(0.0, 2.1, tLocal);
      const retractT = smoothstep(2.2, 4.2, tLocal);
      const armLift = lerp(-0.85, 0.0, lowerT) + lerp(0.0, -0.45, retractT);
      const headTilt = lerp(0.28, 0.20, smoothstep(2.4, 6.8, tLocal));
      const blink = (Math.abs(tLocal - 3.9) < 0.14 || Math.abs(tLocal - 6.2) < 0.12) ? 1 : 0;

      drawAnimatedChild(st, 465, 475, 1.65, {
        armLift,
        headTilt,
        ribbonPhase: tGlobal * 2.2,
        blink,
      });

      // Paper boat: held gently -> touches water at 2.1s with damped splash dip -> drifts smoothly rightward!
      const driftT = smoothstep(2.15, 7.5, tLocal);
      const boatX = 768 + driftT * 470;
      let boatY = 648;
      let boatTilt = 0.03;
      if (tLocal < 2.1) {
        boatY = 648 - (1 - lowerT) * 28;
        boatTilt = -0.05 * (1 - lowerT);
      } else {
        const dt = tLocal - 2.1;
        const dip = Math.exp(-dt * 2.6) * Math.sin(dt * 7.5) * 9.5;
        boatY = 648 + dip + Math.sin(tGlobal * 2.4) * 3.2 - driftT * 26;
        boatTilt = Math.sin(tGlobal * 2.0 + 0.5) * 0.045 + Math.exp(-dt * 2.2) * 0.06;
      }

      drawPaperBoat(st, boatX, boatY, lerp(1.28, 1.12, driftT), {
        tilt: boatTilt, sunFromRight: true, withRipples: tLocal >= 2.0,
      });

      // Expanding launch ripples blooming right after touchdown (2.1s..5.5s)!
      if (tLocal >= 2.05) {
        const rt = tLocal - 2.05;
        for (let k = 0; k < 3; k++) {
          const age = rt - k * 0.55;
          if (age > 0 && age < 3.4) {
            const u = age / 3.4;
            st.ripple(772 + u * 25, 656, 85 + u * 220, 15 + u * 38, { alpha: (1 - u) * 0.65, thickness: 2.0 * (1 - u * 0.4) });
          }
        }
      }

      // Gently swaying overhanging willow branches
      const sway = Math.sin(tGlobal * 1.35) * 0.05;
      drawWillowBranch(st, 1345, -15, 340, -0.18 + sway, { alpha: 0.60, leafCount: 13 });
      drawWillowBranch(st, 1465, -20, 290, -0.12 + sway * 1.2, { alpha: 0.50, leafCount: 11 });
      drawWillowBranch(st, 95, -15, 250, 0.16 + sway * 0.8, { alpha: 0.46, leafCount: 9 });
    });

    // Poetic opening title card fading softly in the upper-right sunlit sky (0.4s..3.8s)
    const titleAlpha = smoothstep(0.4, 1.3, tLocal) * (1 - smoothstep(2.9, 4.0, tLocal));
    if (titleAlpha > 0.01) {
      const ctx = st.ctx;
      ctx.save();
      ctx.globalAlpha = titleAlpha;
      ctx.fillStyle = '#5C4334';
      ctx.font = '500 54px "STKaiti", "KaiTi", "SimSun", "Georgia", serif';
      ctx.textAlign = 'center';
      ctx.fillText('纸船的故事', 1120, 185);
      ctx.font = 'italic 22px "Georgia", serif';
      ctx.fillStyle = '#7E6454';
      ctx.fillText('The Story of a Paper Boat', 1120, 224);
      ctx.restore();
    }
  }

  // ---- SHOT 2: 林荫漂流与小停顿 (7.5s – 14.5s) ----
  _renderShot2(targetCanvas, tLocal, tGlobal) {
    const st = new WatercolorStudio(targetCanvas, 2002);
    const { skyC, horizonY } = this.shots.s2;
    const p = clamp01(tLocal / 7.0);
    const zoom = lerp(1.06, 1.00, easeOutCubic(p));
    const panX = lerp(35, -10, easeOutCubic(p));

    this._applyCamera(st.ctx, zoom, panX, 0, () => {
      this._drawLiveWater(st, skyC, horizonY, tGlobal, {
        tintTop: '#8BD5DC', tintDeep: '#4B9AC0', shadeTint: '#4876A8',
        sunX: 1420, sunWidth: 280, sunColor: '#FFD86B', reflectionAlpha: 0.48, rippleAmp: 10,
      });

      // Gently undulating underwater emerald weeds
      for (let i = 0; i < 6; i++) {
        const wx = 160 + i * 245;
        const wy = 660 + (i % 3) * 70;
        const wSway = Math.sin(tGlobal * 1.4 + i) * 14;
        st.stroke([[wx, wy], [wx + 55, wy - 24 + wSway * 0.4], [wx + 125, wy - 10 + wSway * 0.8], [wx + 180, wy - 32 + wSway]], {
          color: '#388568', width: 15, alpha: 0.25, rimStroke: 0,
        });
      }

      // Mossy river stones
      drawRiverStone(st, 430, 520, 142, 70, { rot: -0.08, moss: true });
      drawRiverStone(st, 240, 620, 112, 54, { rot: 0.12, moss: true });
      drawRiverStone(st, 585, 585, 52, 25, { rot: 0.15, moss: true });

      // Boat drifts smoothly in from left (0..3.4s), gently bumps willow leaf at 3.4s, then bobs & hesitates!
      const arriveT = easeOutCubic(clamp01(tLocal / 3.5));
      const bump = smoothstep(3.3, 4.6, tLocal);
      const pauseWobble = bump * Math.sin((tLocal - 3.3) * 2.1) * 9;
      const boatX = lerp(355, 792, arriveT) + pauseWobble;
      const boatY = 545 + Math.sin(tGlobal * 2.3) * 3.5 + Math.cos(tLocal * 1.4) * 2.0;
      const boatTilt = -0.06 + Math.sin(tGlobal * 1.8) * 0.055;

      // Floating willow leaf gently nudged when boat arrives
      const leafX = 625 + bump * 12 + Math.sin(tGlobal * 1.5) * 3;
      const leafY = 562 + Math.cos(tGlobal * 1.7) * 2.5;
      drawFloatingLeaf(st, leafX, leafY, 1.35, -0.22 + bump * 0.12 + Math.sin(tGlobal * 1.2) * 0.04);

      drawPaperBoat(st, boatX, boatY, 1.48, { tilt: boatTilt, sunFromRight: true, withRipples: true, waterTint: '#4B9AC0' });

      // Subtle swirling eddy ripple around paused boat
      if (tLocal > 3.1) {
        const u = ((tLocal - 3.1) % 2.4) / 2.4;
        st.ripple(750, 575, 115 + u * 130, 22 + u * 26, { alpha: (1 - u) * 0.45, shadow: '#3E7EA8', thickness: 1.6 });
      }

      // Gently swaying reeds & hanging willow curtains
      const sway = Math.sin(tGlobal * 1.25) * 0.055;
      drawReedCluster(st, 130, 695, 9, 365, { lean: 0.22 + sway, alpha: 0.72, width: 12 });
      drawReedCluster(st, 1365, 465, 7, 235, { lean: -0.15 + sway, alpha: 0.60, width: 9 });
      drawWillowBranch(st, 260, -20, 410, 0.18 + sway, { alpha: 0.68, leafCount: 14 });
      drawWillowBranch(st, 450, -25, 330, 0.24 + sway * 1.15, { alpha: 0.58, leafCount: 12 });
      drawReedCluster(st, 65, 940, 5, 255, { lean: 0.35 + sway, colors: ['#3B7E52', '#2E6648'], alpha: 0.52, width: 20 });
    });
  }

  // ---- SHOT 3: 偶遇与轻推 (14.5s – 22.5s) [HERO EMOTIONAL CLIMAX] ----
  _renderShot3(targetCanvas, tLocal, tGlobal) {
    const st = new WatercolorStudio(targetCanvas, 3003);
    const { skyC, horizonY } = this.shots.s3;
    const p = clamp01(tLocal / 8.0);
    const zoom = lerp(1.05, 1.00, easeInOutSine(p));
    const panX = lerp(28, -32, smoothstep(3.6, 8.0, tLocal));

    this._applyCamera(st.ctx, zoom, panX, 0, () => {
      this._drawLiveWater(st, skyC, horizonY, tGlobal, {
        tintTop: '#96DCE0', tintDeep: '#54AAC8', shadeTint: '#4A84B0',
        sunX: 1290, sunWidth: 380, sunColor: '#FFD666', reflectionAlpha: 0.44, rippleAmp: 12,
      });

      // Warm diagonal golden sunbeam breathing gently
      st.glow(1180, 440, 390, 480, '#FFF2BA', 0.32 + Math.sin(tGlobal * 1.1) * 0.04, 'screen', -0.34);

      drawRiverStone(st, 220, 685, 122, 56, { rot: 0.06, moss: true });
      drawFloatingLeaf(st, 1085 + Math.sin(tGlobal * 1.3) * 5, 655 + Math.cos(tGlobal * 1.5) * 3, 1.15, 0.18 + Math.sin(tGlobal) * 0.04);

      const sway = Math.sin(tGlobal * 1.3) * 0.05;
      drawReedCluster(st, 185, 530, 10, 355, { lean: 0.24 + sway, alpha: 0.66, width: 12 });
      drawReedCluster(st, 355, 445, 7, 260, { lean: 0.18 + sway, alpha: 0.50, width: 10 });

      // HERO CHOREOGRAPHY:
      // 0.0..2.2s: Duckling swims in from left reeds (x: 240 -> 595)
      // 2.2..3.5s: Curious pause & adorable head tilt!
      // 3.5..4.3s: Duckling paddles forward & gently nudges paper boat stern at tLocal = 4.1s!
      // 4.1..8.0s: Paper boat rocks forward & glides gracefully into the golden sunlight!
      const swimIn = easeOutCubic(clamp01(tLocal / 2.3));
      const nudgeApproach = smoothstep(3.4, 4.15, tLocal);
      const nudgeFollow = smoothstep(4.15, 5.4, tLocal);
      const duckX = lerp(240, 595, swimIn) + nudgeApproach * 58 - nudgeFollow * 12;
      const duckY = 578 + Math.sin(tGlobal * 3.1) * 3.8;

      let headTilt = 0.02;
      if (tLocal >= 2.0 && tLocal < 3.4) {
        // Curious head-tilt back then forward!
        headTilt = -0.16 * Math.sin(((tLocal - 2.0) / 1.4) * Math.PI);
      } else if (tLocal >= 3.4 && tLocal < 5.0) {
        // Tender forward nudge with bill!
        headTilt = 0.22 * Math.sin(clamp01((tLocal - 3.4) / 1.5) * Math.PI);
      } else if (tLocal >= 5.0) {
        // Proudly watching boat sail away
        headTilt = lerp(0.0, -0.08, smoothstep(5.0, 6.8, tLocal));
      }

      const glideT = easeInOutSine(clamp01((tLocal - 4.05) / 3.95));
      const boatX = 895 + glideT * 365 + (tLocal < 4.05 ? Math.sin(tGlobal * 1.9) * 5 : 0);
      const boatY = 540 + Math.sin(tGlobal * 2.4 + 0.7) * 3.5 - glideT * 18;
      let boatTilt = Math.sin(tGlobal * 2.0) * 0.03;
      if (tLocal >= 4.0 && tLocal < 6.0) {
        const dt = tLocal - 4.0;
        boatTilt += Math.exp(-dt * 2.0) * Math.sin(dt * 5.2) * 0.13;
      }

      drawFluffyDuckling(st, duckX, duckY, 2.05, { facingRight: true, headTilt, withRipples: true, sunFromRight: true });
      drawPaperBoat(st, boatX, boatY, 1.62, { tilt: boatTilt, sunFromRight: true, withRipples: true, waterTint: '#54AAC8' });

      // Tender contact ripple blooming right where bill touches stern (tLocal >= 4.05s)!
      if (tLocal >= 4.0) {
        const rt = tLocal - 4.0;
        for (let k = 0; k < 2; k++) {
          const age = rt - k * 0.45;
          if (age > 0 && age < 2.8) {
            const u = age / 2.8;
            st.ripple(788 + u * 35, 558, 35 + u * 185, 8 + u * 32, { alpha: (1 - u) * 0.80, thickness: 2.2 * (1 - u * 0.35) });
          }
        }
      }

      // Framing willow & foreground reeds
      drawWillowBranch(st, 140, -15, 320, 0.20 + sway, { alpha: 0.60, leafCount: 12 });
      drawReedCluster(st, 75, 935, 6, 285, { lean: 0.30 + sway, colors: ['#4A9154', '#38764C'], alpha: 0.50, width: 22 });
      drawReedCluster(st, 1525, 945, 4, 215, { lean: -0.25 + sway, colors: ['#B0D460', '#74B254'], alpha: 0.42, width: 18 });
    });
  }

  // ---- SHOT 4: 驶向阳光 (22.5s – 30.0s) [POETIC FINALE] ----
  _renderShot4(targetCanvas, tLocal, tGlobal) {
    const st = new WatercolorStudio(targetCanvas, 4004);
    const { skyC, horizonY } = this.shots.s4;
    const p = clamp01(tLocal / 7.5);
    const zoom = lerp(1.07, 0.99, easeInOutSine(p));
    const panY = lerp(-18, 12, easeInOutSine(p));

    this._applyCamera(st.ctx, zoom, 0, panY, () => {
      this._drawLiveWater(st, skyC, horizonY, tGlobal, {
        tintTop: '#A4E0DE', tintDeep: '#5FB2CE', shadeTint: '#4D8BB8',
        sunX: 1165, sunWidth: 440, sunColor: '#FFD266', reflectionAlpha: 0.48, rippleAmp: 12,
      });
      st.glow(1100, 620, 420, 210, '#FFC478', 0.34, 'multiply', 0.04);
      st.glow(280, 720, 390, 210, '#4684AE', 0.28, 'multiply');

      // Paper boat sailing gracefully toward the glowing golden horizon!
      const sail = easeInOutSine(p);
      const boatX = lerp(850, 1185, sail);
      const boatY = lerp(522, 428, sail) + Math.sin(tGlobal * 2.2) * 2.2;
      const boatScale = lerp(0.86, 0.44, sail);

      // Shimmering undulating twin white V-wake trailing smoothly behind the boat
      st.ctx.save();
      st.ctx.globalCompositeOperation = 'screen';
      st.ctx.lineCap = 'round';
      const drawWake = (dx1, dy1, dx2, dy2, bw, ba) => {
        const steps = 6;
        for (let i = 0; i < steps; i++) {
          const t0 = i / steps, t1 = (i + 1) / steps;
          const x0 = boatX + dx1 * t0 + Math.sin(tGlobal * 2.5 + i) * 2.5;
          const y0 = boatY + 8 * boatScale + dy1 * t0;
          const x1 = boatX + dx1 * t1 + Math.sin(tGlobal * 2.5 + i + 1) * 2.5;
          const y1 = boatY + 8 * boatScale + dy1 * t1;
          st.ctx.strokeStyle = `rgba(255,254,248,${ba * (1 - t0) * (1 - t0 * 0.4)})`;
          st.ctx.lineWidth = Math.max(0.7, bw * (1 - t0 * 0.65));
          st.ctx.beginPath();
          st.ctx.moveTo(x0, y0);
          st.ctx.lineTo(x1, y1);
          st.ctx.stroke();
        }
      };
      drawWake(-230 * boatScale, 88 * boatScale, 0, 0, 3.0, 0.78);
      drawWake(-165 * boatScale, 128 * boatScale, 0, 0, 2.8, 0.68);
      st.ctx.restore();

      drawPaperBoat(st, boatX, boatY, boatScale, {
        tilt: -0.03 + Math.sin(tGlobal * 1.9) * 0.025, sunFromRight: true, withRipples: true, waterTint: '#F2CC74',
      });
      st.glow(boatX, boatY - 6, 105 * boatScale + 35, 60 * boatScale + 20, '#FFFDF5', 0.56, 'screen');

      // Duckling in foreground left, bobbing peacefully and watching the boat sail into the sun!
      const duckY = 705 + Math.sin(tGlobal * 2.3) * 3.0;
      const duckTilt = -0.07 - sail * 0.04;
      drawFluffyDuckling(st, 405, duckY, 1.32, { facingRight: true, headTilt: duckTilt, withRipples: true, sunFromRight: true });

      // Floating warm afternoon bokeh orbs drifting gently upward in the sunlight!
      for (let i = 0; i < 18; i++) {
        const bx = 760 + ((i * 83) % 740) + Math.sin(tGlobal * 0.6 + i) * 18;
        const by = 420 - ((tGlobal * (10 + (i % 5) * 4) + i * 37) % 340);
        const br = 10 + (i % 6) * 4.5;
        const ba = (0.22 + 0.25 * Math.sin(tGlobal * 1.5 + i)) * (1 - Math.abs((by - 250) / 220));
        if (ba > 0.04) st.glow(bx, by, br, br, '#FFFDF4', ba, 'screen');
      }

      // Framing mossy stone, gently swaying reeds & willow
      const sway = Math.sin(tGlobal * 1.2) * 0.045;
      drawRiverStone(st, 145, 795, 108, 46, { rot: 0.12, moss: true });
      drawReedCluster(st, 110, 910, 10, 365, { lean: 0.25 + sway, alpha: 0.64, width: 14 });
      drawWillowBranch(st, 180, -15, 350, 0.22 + sway, { alpha: 0.58, leafCount: 13 });
      drawWillowBranch(st, 340, -20, 270, 0.18 + sway * 1.1, { alpha: 0.48, leafCount: 10 });
    });

    // Gentle warm cream-paper finale fade & poetic "— 完 —" end mark (27.4s..30.0s -> tLocal 4.9..7.5)
    const fadeOut = smoothstep(5.4, 7.3, tLocal);
    if (fadeOut > 0.005) {
      st.ctx.save();
      st.ctx.fillStyle = `rgba(252, 249, 241, ${fadeOut})`;
      st.ctx.fillRect(0, 0, this.w, this.h);
      st.ctx.restore();
    }
    const endAlpha = smoothstep(5.0, 5.9, tLocal) * (1 - smoothstep(6.7, 7.45, tLocal));
    if (endAlpha > 0.01) {
      st.ctx.save();
      st.ctx.globalAlpha = endAlpha;
      st.ctx.fillStyle = '#6E5544';
      st.ctx.font = '500 38px "STKaiti", "KaiTi", "SimSun", serif';
      st.ctx.textAlign = 'center';
      st.ctx.fillText('— 完 —', this.w * 0.5, this.h * 0.5 + 10);
      st.ctx.restore();
    }
  }

  // Render exact frame at time tSec (0.0 .. 30.0) onto targetCanvas with smooth cross-dissolves!
  renderFrame(targetCanvas, tSec) {
    const ctx = targetCanvas.getContext('2d');
    const D = 0.65; // silky 0.65s watercolor cross-dissolve duration

    // Shot boundaries: S1 [0..7.5], S2 [7.5..14.5], S3 [14.5..22.5], S4 [22.5..30.0]
    let warmth = 0.06;
    if (tSec < 7.5 - D) {
      this._renderShot1(targetCanvas, tSec, tSec);
    } else if (tSec < 7.5) {
      const mix = smoothstep(7.5 - D, 7.5, tSec);
      this._renderShot1(this.bufA, tSec, tSec);
      this._renderShot2(this.bufB, tSec - (7.5 - D), tSec);
      ctx.drawImage(this.bufA, 0, 0);
      ctx.save(); ctx.globalAlpha = mix; ctx.drawImage(this.bufB, 0, 0); ctx.restore();
    } else if (tSec < 14.5 - D) {
      this._renderShot2(targetCanvas, tSec - 7.5 + D, tSec);
      warmth = 0.04;
    } else if (tSec < 14.5) {
      const mix = smoothstep(14.5 - D, 14.5, tSec);
      this._renderShot2(this.bufA, tSec - 7.5 + D, tSec);
      this._renderShot3(this.bufB, tSec - (14.5 - D), tSec);
      ctx.drawImage(this.bufA, 0, 0);
      ctx.save(); ctx.globalAlpha = mix; ctx.drawImage(this.bufB, 0, 0); ctx.restore();
    } else if (tSec < 22.5 - D) {
      this._renderShot3(targetCanvas, tSec - 14.5 + D, tSec);
      warmth = 0.07;
    } else if (tSec < 22.5) {
      const mix = smoothstep(22.5 - D, 22.5, tSec);
      this._renderShot3(this.bufA, tSec - 14.5 + D, tSec);
      this._renderShot4(this.bufB, tSec - (22.5 - D), tSec);
      ctx.drawImage(this.bufA, 0, 0);
      ctx.save(); ctx.globalAlpha = mix; ctx.drawImage(this.bufB, 0, 0); ctx.restore();
    } else {
      this._renderShot4(targetCanvas, tSec - 22.5 + D, tSec);
      warmth = 0.09;
    }

    // Opening warm paper fade-in (0.0s .. 0.9s)
    if (tSec < 0.9) {
      const fi = 1 - smoothstep(0.0, 0.9, tSec);
      ctx.save();
      ctx.fillStyle = `rgba(252, 249, 241, ${fi})`;
      ctx.fillRect(0, 0, this.w, this.h);
      ctx.restore();
    }

    // Apply fast, flicker-free optical Arches 300gsm watercolor paper texture!
    this._applyFastPaperPhysics(targetCanvas, warmth);
  }
}
