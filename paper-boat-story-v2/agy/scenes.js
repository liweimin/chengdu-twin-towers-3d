// scenes.js
// 4 Luminous, joyful children's picture-book watercolor keyframes for 《纸船的故事》

import { WatercolorCanvas, ellipsePoints } from './watercolor_engine.js';
import {
  PALETTE,
  drawPaperBoat,
  drawDuckling,
  drawChildByBank,
  drawRiverStone,
  drawFloatingLeaf,
  drawReedCluster,
  drawWillowBranch,
  drawWildflower,
  drawWaterSparkles,
} from './characters.js';

// Sparkling transparent turquoise-cerulean watercolor stream with tapered brushstroke ribbons
function paintStreamBase(wc, yTop, yBottom, colors, seedBias = 0) {
  const w = wc.w;
  // Clean sky-aqua base glaze
  wc.bloom(w * 0.5, (yTop + yBottom) * 0.5, w * 0.65, (yBottom - yTop) * 0.68, colors[0], 0.55, 'multiply');

  // Tapered, organic silk-like watercolor current brushstrokes (NO blunt rectangular ends!)
  const ribbons = 15;
  for (let i = 0; i < ribbons; i++) {
    const t = (i + 0.4) / ribbons;
    const y = yTop + (yBottom - yTop) * t + wc.rng.range(-15, 15);
    const x0 = wc.rng.range(-120, w * 0.35);
    const x1 = wc.rng.range(w * 0.58, w + 120);
    const len = x1 - x0;
    const thick = wc.rng.range(16, 36);
    const wave = Math.sin(i * 1.4 + seedBias) * 14;
    const pts = [
      [x0, y],
      [x0 + len * 0.18, y - thick * 0.36 + wave * 0.4],
      [x0 + len * 0.50, y - thick * 0.50 + wave],
      [x0 + len * 0.82, y - thick * 0.32 + wave * 0.4],
      [x1, y],
      [x0 + len * 0.82, y + thick * 0.34 + wave * 0.4],
      [x0 + len * 0.50, y + thick * 0.46 + wave],
      [x0 + len * 0.18, y + thick * 0.32 + wave * 0.4],
    ];
    wc.wash(pts, {
      color: i % 3 === 0 ? colors[2] : colors[1],
      alpha: wc.rng.range(0.20, 0.34),
      layers: 5,
      variance: 0.08,
      blur: 2.2,
      edgeDarken: 0.20,
      granulation: 0.26,
      composite: 'multiply',
    });
  }
}

// ============================================================================
// KEYFRAME 1: 入水与启程 (0–6s)
// Sunlit spring meadow, adorable child in blue overalls releasing paper boat into sparkling turquoise stream
// ============================================================================
export function renderKF1Launch(canvas) {
  const wc = new WatercolorCanvas(canvas, 1011);
  const w = wc.w, h = wc.h;

  // 1. Clear bright summer sky wash (pale cerulean + sunlit lemon-cream)
  wc.bloom(520, 120, 620, 260, '#BEE3F5', 0.42, 'multiply');
  wc.bloom(1220, 120, 520, 250, '#FFE99E', 0.46, 'multiply');
  wc.sunHighlight(1260, 110, 280, 160, '#FFFDF5', 0.65, 0, 18);

  // Crisp-edged hand-painted watercolor background trees & bushes (NOT blurry ink blobs!)
  wc.foliageDabs(1020, 220, 260, 110, 38, ['#C8DF6B', '#88C262', '#64AE63', '#A8D872'], {
    dabMin: 18, dabMax: 44, alpha: 0.42, blur: 1.2, edgeDarken: 0.32,
  });
  wc.foliageDabs(1420, 210, 240, 115, 34, ['#D9E36E', '#8FC464', '#69AF5E'], {
    dabMin: 18, dabMax: 42, alpha: 0.40, blur: 1.2, edgeDarken: 0.30,
  });
  wc.foliageDabs(260, 210, 250, 95, 28, ['#B9DA6E', '#7AB962', '#9ED074'], {
    dabMin: 16, dabMax: 38, alpha: 0.34, blur: 1.4, edgeDarken: 0.28,
  });

  // 2. Sparkling cerulean-turquoise stream
  paintStreamBase(wc, 315, h, ['#9EE0E0', '#63B8D4', '#86C9D8'], 1);

  // Warm golden sunlit water reflection on the right
  wc.bloom(1260, 520, 340, 160, PALETTE.waterGold, 0.36, 'multiply', -0.05);
  wc.sunHighlight(1310, 490, 270, 100, '#FFFDF4', 0.56, -0.04, 14);

  // Submerged warm colorful pebbles visible through crystal-clear shallow water
  for (let i = 0; i < 8; i++) {
    const px = wc.rng.range(760, 1480);
    const py = wc.rng.range(540, 840);
    wc.wash(ellipsePoints(px, py, wc.rng.range(20, 44), wc.rng.range(10, 20), 12, wc.rng.range(-0.2, 0.2)), {
      color: i % 2 === 0 ? '#C9B898' : '#8BAAC0',
      alpha: 0.28,
      layers: 4,
      blur: 2.2,
      edgeDarken: 0.14,
    });
  }

  // 3. Lush sunlit spring-green grassy stream bank on the left
  const bankPts = [
    [-40, 285], [320, 295], [585, 350], [700, 445], [655, 585],
    [520, 745], [350, 920], [-40, 920],
  ];
  wc.gouache(bankPts, '#FCF9EE', 0.90, 1.0);
  wc.wash(bankPts, {
    color: PALETTE.meadowLight,
    color2: PALETTE.meadowMid,
    alpha: 0.72,
    layers: 10,
    variance: 0.08,
    edgeDarken: 0.34,
    granulation: 0.32,
    blur: 0.8,
  });
  // Crisp juicy sunlit yellow-green & emerald watercolor grass dabs on the bank!
  wc.foliageDabs(290, 560, 270, 210, 46, [PALETTE.meadowSun, PALETTE.meadowLight, PALETTE.meadowMid, '#E6E276'], {
    dabMin: 16, dabMax: 38, alpha: 0.42, blur: 0.7, edgeDarken: 0.30,
  });

  // River stones along the bank edge
  drawRiverStone(wc, 615, 490, 44, 24, { rot: 0.14, moss: true });
  drawRiverStone(wc, 555, 625, 56, 26, { rot: -0.08, moss: true });

  // Cheerful grass blades & colorful spring wildflowers (white daisies, buttercups, forget-me-nots!)
  drawReedCluster(wc, 130, 450, 9, 135, { lean: 0.18, alpha: 0.62, width: 8 });
  drawReedCluster(wc, 545, 415, 7, 110, { lean: 0.24, alpha: 0.56, width: 7 });
  drawWildflower(wc, 175, 575, 1.25, '#FFFFFF', '#FFC53D');
  drawWildflower(wc, 228, 628, 1.05, '#FFE47A', '#E88E38');
  drawWildflower(wc, 125, 665, 1.00, '#A8D4FF', '#FFE066');
  drawWildflower(wc, 285, 742, 1.15, '#FFFFFF', '#FFC53D');
  drawWildflower(wc, 465, 540, 0.95, '#FFD1CC', '#FFE066');
  drawWildflower(wc, 375, 685, 1.00, '#A8D4FF', '#FFE066');

  // 4. Perfected adorable storybook child squatting on mossy bank & releasing paper boat!
  drawChildByBank(wc, 465, 478, 1.64);

  // 5. Crisp cream paper boat just touching the turquoise water right beside the child's fingers!
  drawPaperBoat(wc, 795, 650, 1.28, {
    tilt: 0.04,
    sunFromRight: true,
    withReflection: true,
    withRipples: true,
  });

  // Expanding watercolor launch ripples
  wc.ripple(795, 662, 172, 30, { alpha: 0.52, thickness: 2.0 });
  wc.ripple(799, 666, 242, 42, { alpha: 0.30, thickness: 1.5 });

  // Sparkling white water highlights dancing toward the sunlit right
  drawWaterSparkles(wc, 990, 405, 1520, 795, 52, 20);

  // 6. Fresh overhanging sunlit willow branches
  drawWillowBranch(wc, 1340, -10, 320, -0.18, { alpha: 0.58, blur: 0.7, leafCount: 12 });
  drawWillowBranch(wc, 1465, -15, 270, -0.12, { alpha: 0.48, blur: 1.0, leafCount: 10 });
  drawWillowBranch(wc, 105, -10, 230, 0.15, { alpha: 0.45, blur: 1.0, leafCount: 8 });

  // Joyful watercolor pigment splatters (golden yellow & turquoise)
  wc.splatter(1180, 460, 180, 18, '#F5BE42', 0.35);
  wc.splatter(920, 730, 160, 14, '#5CB3D0', 0.30);

  wc.finishPictureBook(0.06, true);
}

// ============================================================================
// KEYFRAME 2: 林荫漂流与小停顿 (6–13s)
// Cool turquoise-cobalt shaded bend (luminous watercolor shade, NOT grey ink!),
// mossy stones & willow leaf catching the boat, warm golden sunlight gleaming ahead
// ============================================================================
export function renderKF2Eddy(canvas) {
  const wc = new WatercolorCanvas(canvas, 2022);
  const w = wc.w, h = wc.h;

  // 1. Fresh cool sky & sunlit clearing on far right
  wc.bloom(420, 130, 560, 230, '#B8DFEE', 0.42, 'multiply');
  wc.bloom(1420, 170, 340, 210, '#FFE48C', 0.55, 'multiply');
  wc.sunHighlight(1440, 165, 240, 140, '#FFFDF4', 0.68, 0, 18);

  // Crisp layered watercolor canopy foliage dabs (viridian, spring green, turquoise-green)
  wc.foliageDabs(290, 130, 340, 155, 52, ['#62AB64', '#468E68', '#8CC76C', '#52987E'], {
    dabMin: 20, dabMax: 48, alpha: 0.44, blur: 1.2, edgeDarken: 0.32,
  });
  wc.foliageDabs(790, 120, 310, 130, 42, ['#77BA6A', '#569C72', '#A8D46E', '#67A88C'], {
    dabMin: 18, dabMax: 44, alpha: 0.38, blur: 1.4, edgeDarken: 0.30,
  });

  // 2. Luminous shaded cerulean-cobalt & turquoise stream
  paintStreamBase(wc, 265, h, ['#8AD2DA', '#4E9EC2', '#5B84B8'], 2);

  // Translucent emerald underwater swaying waterweeds
  for (let i = 0; i < 6; i++) {
    const wx = 160 + i * 245 + wc.rng.range(-40, 40);
    const wy = wc.rng.range(640, 860);
    wc.brushStroke([[wx, wy], [wx + 55, wy - 25], [wx + 125, wy - 12], [wx + 180, wy - 35]], {
      color: '#3D8C6D',
      width: 15,
      alpha: 0.28,
      blur: 2.8,
    });
  }

  // Warm golden sunlit water beckoning on the far right
  wc.bloom(1430, 440, 260, 155, PALETTE.waterGold, 0.42, 'multiply', -0.08);
  wc.sunHighlight(1450, 410, 220, 95, '#FFFDF4', 0.58, -0.06, 14);

  // 3. Mossy river stones forming the quiet eddy
  drawRiverStone(wc, 430, 520, 142, 70, { rot: -0.08, moss: true });
  drawRiverStone(wc, 240, 620, 112, 54, { rot: 0.12, moss: true });
  drawRiverStone(wc, 585, 585, 52, 25, { rot: 0.15, moss: true });

  wc.ripple(725, 580, 165, 32, { alpha: 0.46, shadowColor: '#4384AE', thickness: 1.8 });
  wc.ripple(710, 588, 235, 46, { alpha: 0.28, shadowColor: '#4384AE', thickness: 1.5 });

  // 4. Sunlit green willow leaf catching the paper boat's bow
  drawFloatingLeaf(wc, 625, 562, 1.35, -0.22);

  // 5. Crisp cream paper boat paused in the shaded cobalt-turquoise eddy
  drawPaperBoat(wc, 795, 545, 1.48, {
    tilt: -0.08,
    sunFromRight: true,
    withReflection: true,
    withRipples: true,
    waterTint: '#4E9EC2',
  });

  // 6. Fresh watercolor reeds & hanging willow leaves
  drawReedCluster(wc, 130, 690, 9, 360, { lean: 0.22, color: '#6FB55C', color2: '#3E8759', alpha: 0.65, blur: 0.6, width: 12 });
  drawReedCluster(wc, 1360, 460, 7, 230, { lean: -0.15, color: '#9FD062', color2: '#5AA358', alpha: 0.56, blur: 0.8, width: 9 });
  drawWillowBranch(wc, 280, -20, 390, 0.18, { color: '#78B95B', color2: '#4B9459', alpha: 0.64, blur: 0.6, leafCount: 14 });
  drawWillowBranch(wc, 460, -25, 310, 0.24, { color: '#97CB62', color2: '#5DA65C', alpha: 0.54, blur: 0.9, leafCount: 11 });

  drawReedCluster(wc, 70, 940, 5, 250, { lean: 0.35, color: '#458B59', color2: '#357052', alpha: 0.48, blur: 3.5, width: 20 });

  drawWaterSparkles(wc, 1180, 340, 1550, 640, 34, 16);
  wc.splatter(690, 640, 190, 16, '#4E9EC2', 0.28);

  wc.finishPictureBook(0.05, true);
}

// ============================================================================
// KEYFRAME 3: 偶遇与轻推 (13–21s) [HERO FRAME]
// Fluffy golden-buttercup duckling nudges cream paper boat out of cool turquoise shade into warm sunlit gold!
// ============================================================================
export function renderKF3Nudge(canvas) {
  const wc = new WatercolorCanvas(canvas, 3033);
  const w = wc.w, h = wc.h;

  // 1. Vibrant watercolor background: cool turquoise-mint shade left -> luminous golden-peach afternoon light right
  wc.bloom(360, 150, 520, 240, '#B2DCE6', 0.44, 'multiply');
  wc.bloom(1250, 140, 520, 260, '#FFE084', 0.52, 'multiply');
  wc.bloom(1480, 210, 280, 170, '#FFB884', 0.36, 'multiply');
  wc.sunHighlight(1340, 120, 320, 180, '#FFFDF5', 0.72, 0, 20);

  // Crisp botanical background foliage dabs on the left bank
  wc.foliageDabs(280, 190, 310, 140, 44, ['#7AC066', '#56A266', '#A7D66E', '#62AE82'], {
    dabMin: 18, dabMax: 42, alpha: 0.40, blur: 1.2, edgeDarken: 0.30,
  });

  // Warm golden diagonal sunbeam
  wc.bloom(1180, 420, 380, 460, '#FFF2B8', 0.30, 'screen', -0.32);

  // 2. Sparkling turquoise -> sunlit aqua-gold stream
  paintStreamBase(wc, 290, h, ['#96DCE0', '#5CB3D0', '#7FC8D4'], 3);
  wc.bloom(320, 560, 420, 230, '#4F8BB8', 0.28, 'multiply');
  wc.bloom(1260, 560, 420, 210, PALETTE.waterGold, 0.42, 'multiply', -0.05);
  wc.sunHighlight(1310, 520, 320, 135, '#FFFDF5', 0.58, -0.06, 16);

  // Mossy stone & floating leaf
  drawRiverStone(wc, 220, 680, 122, 56, { rot: 0.06, moss: true });
  drawFloatingLeaf(wc, 1085, 655, 1.15, 0.18);

  // Fresh green watercolor reeds on the left
  drawReedCluster(wc, 190, 520, 10, 350, { lean: 0.24, color: '#87C45E', color2: '#4E985A', alpha: 0.58, blur: 0.9, width: 12 });
  drawReedCluster(wc, 360, 440, 7, 260, { lean: 0.18, color: '#AED66A', color2: '#68AF5E', alpha: 0.46, blur: 1.4, width: 10 });

  // 3. HERO INTERACTION: Duckling tenderly nudging the paper boat's stern!
  const duckScale = 2.05;
  const boatScale = 1.62;
  drawDuckling(wc, 646, 578, duckScale, {
    facingRight: true,
    headTilt: 0.18,
    withReflection: true,
    withRipples: true,
    sunFromRight: true,
  });

  drawPaperBoat(wc, 916, 540, boatScale, {
    tilt: 0.08,
    sunFromRight: true,
    withReflection: true,
    withRipples: true,
    waterTint: '#5CB3D0',
  });

  wc.ripple(788, 558, 42, 9, { alpha: 0.78, thickness: 2.0 });
  wc.ripple(922, 558, 175, 30, { alpha: 0.50, thickness: 1.9 });
  wc.ripple(638, 598, 165, 28, { alpha: 0.44, thickness: 1.7 });

  drawWaterSparkles(wc, 1060, 420, 1540, 760, 54, 22);

  // 4. Framing willow & soft foreground reeds
  drawWillowBranch(wc, 145, -15, 310, 0.20, { color: '#84C15E', color2: '#529B56', alpha: 0.56, blur: 1.0, leafCount: 11 });
  drawReedCluster(wc, 75, 935, 6, 280, { lean: 0.30, color: '#4F9656', color2: '#3B7B50', alpha: 0.46, blur: 3.5, width: 22 });
  drawReedCluster(wc, 1520, 945, 4, 210, { lean: -0.25, color: '#B4D664', color2: '#7BB658', alpha: 0.38, blur: 3.8, width: 18 });

  wc.splatter(1120, 430, 210, 20, '#F5BD44', 0.34);
  wc.splatter(480, 660, 160, 14, '#5CB3D0', 0.28);

  wc.finishPictureBook(0.07, true);
}

// ============================================================================
// KEYFRAME 4: 驶向阳光 (21–30s)
// Poetic wide storybook view: luminous golden-peach afternoon sky & sparkling stream,
// tiny bright cream boat sailing into the light while duckling watches from left bank
// ============================================================================
export function renderKF4Sunlight(canvas) {
  const wc = new WatercolorCanvas(canvas, 4044);
  const w = wc.w, h = wc.h;

  // 1. Luminous warm golden-lemon & soft coral-peach horizon sky
  wc.bloom(420, 150, 580, 260, '#C8E6F2', 0.34, 'multiply');
  wc.bloom(1180, 190, 560, 290, '#FFDF82', 0.54, 'multiply');
  wc.bloom(1380, 160, 360, 220, '#FFB58A', 0.38, 'multiply');
  wc.sunHighlight(1190, 195, 380, 210, '#FFFDF6', 0.78, 0, 24);

  // Soft sunlit watercolor foliage dabs framing the far distant river bend
  wc.foliageDabs(240, 235, 320, 120, 38, ['#8AC26C', '#67AE6A', '#B5DA74'], {
    dabMin: 18, dabMax: 42, alpha: 0.38, blur: 1.6, edgeDarken: 0.26,
  });
  wc.foliageDabs(1490, 265, 220, 95, 24, ['#D8DC76', '#A8CC6E', '#F2CB7C'], {
    dabMin: 16, dabMax: 36, alpha: 0.34, blur: 1.6, edgeDarken: 0.24,
  });

  // 2. Sparkling wide turquoise-aqua stream opening into warm golden light
  paintStreamBase(wc, 325, h, ['#9EE0E0', '#64B6D2', '#8CD2D8'], 4);

  // Organic glowing golden-peach sunlight reflection across the right-center water
  wc.bloom(1180, 440, 390, 175, '#FFD666', 0.48, 'multiply', -0.06);
  wc.bloom(1100, 620, 440, 210, '#FFC67A', 0.40, 'multiply', 0.04);
  wc.bloom(1360, 720, 340, 190, '#FFB885', 0.34, 'multiply');
  wc.sunHighlight(1140, 490, 360, 180, '#FFFDF5', 0.66, -0.1, 22);
  wc.sunHighlight(1060, 620, 300, 135, '#FFFDF2', 0.46, -0.05, 18);

  // Cool cerulean-teal shade pocket on foreground left
  wc.bloom(280, 720, 390, 210, '#4E8FB8', 0.32, 'multiply');

  // 3. Delicate undulating white V-wake ripples behind the departing paper boat
  wc.ctx.save();
  wc.ctx.globalCompositeOperation = 'screen';
  wc.ctx.lineCap = 'round';
  const drawWakeCurve = (pts, baseWidth, baseAlpha) => {
    for (let i = 0; i < pts.length - 1; i++) {
      const t = i / (pts.length - 1);
      const fade = (1 - t) * (1 - t * 0.5);
      wc.ctx.strokeStyle = `rgba(255, 254, 248, ${baseAlpha * fade})`;
      wc.ctx.lineWidth = Math.max(0.8, baseWidth * (1 - t * 0.65));
      wc.ctx.beginPath();
      wc.ctx.moveTo(pts[i][0], pts[i][1]);
      wc.ctx.lineTo(pts[i + 1][0], pts[i + 1][1]);
      wc.ctx.stroke();
    }
  };
  drawWakeCurve([[985, 488], [945, 502], [902, 514], [858, 532], [810, 548], [755, 570]], 3.2, 0.78);
  drawWakeCurve([[1012, 492], [982, 512], [952, 534], [918, 558], [882, 584], [842, 614]], 3.0, 0.70);
  wc.ctx.restore();
  wc.ripple(965, 504, 58, 10, { alpha: 0.48, thickness: 1.5 });
  wc.ripple(910, 536, 78, 14, { alpha: 0.30, thickness: 1.2 });

  // 4. Tiny bright cream paper boat sailing into the golden sunlight
  drawPaperBoat(wc, 1025, 475, 0.72, {
    tilt: -0.03,
    sunFromRight: true,
    withReflection: true,
    withRipples: true,
    waterTint: '#F2CC74',
  });
  wc.sunHighlight(1025, 468, 95, 55, '#FFFDF5', 0.48, 0, 14);

  // 5. Duckling in foreground left, floating peacefully and watching it go
  drawDuckling(wc, 405, 705, 1.32, {
    facingRight: true,
    headTilt: -0.08,
    withReflection: true,
    withRipples: true,
    sunFromRight: true,
  });

  // 6. Dancing white sunlit sparkles & floating warm bokeh circles
  drawWaterSparkles(wc, 780, 355, 1520, 740, 76, 24);
  for (let i = 0; i < 18; i++) {
    const bx = wc.rng.range(760, 1500);
    const by = wc.rng.range(90, 420);
    const br = wc.rng.range(10, 34);
    wc.sunHighlight(bx, by, br, br, '#FFFDF4', wc.rng.range(0.22, 0.48), 0, 4);
  }

  // 7. Framing mossy left bank edge, fresh reeds & overhanging willow
  drawRiverStone(wc, 145, 795, 108, 46, { rot: 0.12, moss: true });
  drawReedCluster(wc, 110, 910, 9, 360, { lean: 0.25, color: '#78BA5E', color2: '#468E58', alpha: 0.58, blur: 1.2, width: 14 });
  drawWillowBranch(wc, 180, -15, 340, 0.22, { color: '#8BC460', color2: '#559E58', alpha: 0.54, blur: 1.0, leafCount: 12 });
  drawWillowBranch(wc, 340, -20, 260, 0.18, { color: '#A5D46B', color2: '#68AE5E', alpha: 0.44, blur: 1.4, leafCount: 9 });

  wc.splatter(1120, 390, 260, 24, '#F5BA45', 0.34);
  wc.splatter(350, 760, 150, 12, '#5BB0CE', 0.26);

  wc.finishPictureBook(0.10, true);
}

// Dedicated fast character-study scene for inspecting & refining the child up close
export function renderChildStudy(canvas) {
  const wc = new WatercolorCanvas(canvas, 999);
  // Simple subtle sunlit grass & water hint so we see proportion & interaction clearly
  wc.bloom(520, 740, 420, 120, '#A8D46E', 0.38, 'multiply');
  wc.bloom(1140, 720, 440, 140, '#8AD8DC', 0.42, 'multiply');
  drawChildByBank(wc, 620, 460, 2.05);
  drawPaperBoat(wc, 1060, 685, 1.45, { tilt: 0.04, sunFromRight: true, withReflection: true, withRipples: true });
  wc.finishPictureBook(0.04, false);
}

export const SCENES = {
  kf1_launch: renderKF1Launch,
  kf2_eddy: renderKF2Eddy,
  kf3_nudge: renderKF3Nudge,
  kf4_sunlight: renderKF4Sunlight,
  child_study: renderChildStudy,
};
