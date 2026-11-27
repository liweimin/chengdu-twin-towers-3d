// scenes_v2.js
// Studio-grade full-bleed Ghibli / European watercolor picture-book keyframes for 《纸船的故事》

import { WatercolorStudio, ellipsePts } from './watercolor_v2.js';
import {
  drawPaperBoat,
  drawFluffyDuckling,
  drawStorybookChild,
  drawRiverStone,
  drawFloatingLeaf,
  drawReedCluster,
  drawWillowBranch,
  drawWildflower,
} from './characters_v2.js';

// ============================================================================
// KEYFRAME 1: 入水与启程 (0–6s)
// Full-bleed sunlit summer meadow & shimmering mirror-reflected stream;
// adorable child in straw sunhat & sky-blue smock crouching on wildflower bank releasing paper boat!
// ============================================================================
export function renderKF1Launch(canvas) {
  const st = new WatercolorStudio(canvas, 5011);
  const w = st.w, h = st.h;
  const horizonY = 335;

  // 1. Luminous sky + soft cumulus clouds + warm afternoon sun
  st.paintSky(horizonY, {
    topColor: '#86C7E8',
    midColor: '#C8EAF6',
    horizonColor: '#FFF3C4',
    sunX: 1290,
    sunY: 115,
    sunColor: '#FFE082',
    cloudCount: 4,
  });

  // 2. Layered atmospheric distant hills & sunlit wooded far bank
  st.paintDistantHills(horizonY, [
    { color: '#9CC6C2', color2: '#89B5C4', alpha: 0.42, amp: 58, yOff: -12, freq: 0.0024, phase: 0.5, blur: 3.5 },
    { color: '#8EC47E', color2: '#6DAA6E', alpha: 0.58, amp: 36, yOff: 2, freq: 0.0038, phase: 2.1, blur: 2.0 },
  ]);

  // 3. Rich 3-value painterly trees with varied leans & bushy shoreline bases!
  st.paintTree(1060, horizonY + 8, 1.02, { sunFromRight: true, alpha: 0.78, lean: -18 });
  st.paintTree(1380, horizonY + 10, 1.24, { sunFromRight: true, alpha: 0.82, lean: 22 });
  st.paintTree(795, horizonY + 5, 0.76, { sunFromRight: true, alpha: 0.62, lean: 14 });
  st.paintTree(235, horizonY + 6, 0.92, { sunFromRight: true, alpha: 0.72, lean: -12 });

  // 4. MAGIC MIRROR-REFLECTION STREAM! (Reflects sky, clouds, trees & golden sun!)
  st.paintWaterWithReflection(horizonY, {
    tintTop: '#9CE0E2',
    tintDeep: '#55ABC9',
    shadeTint: '#4D8BB8',
    sunX: 1280,
    sunWidth: 360,
    sunColor: '#FFD96B',
    reflectionAlpha: 0.44,
    rippleAmp: 12,
  });

  // Submerged warm river pebbles visible through clear shallow creek water
  for (let i = 0; i < 10; i++) {
    const px = st.rng.range(720, 1480);
    const py = st.rng.range(540, 845);
    st.wash(ellipsePts(px, py, st.rng.range(18, 42), st.rng.range(9, 18), 12, st.rng.range(-0.2, 0.2)), {
      color: i % 2 === 0 ? '#C9B38C' : '#7FA3BC', alpha: 0.28, layers: 3, blur: 2.4, rimStroke: 0,
    });
  }

  // 5. Lush sunlit wildflower meadow bank on the left (layered values + dappled canopy shadows!)
  const bankPts = [
    [-40, 310], [290, 322], [560, 370], [678, 455], [642, 595],
    [510, 750], [345, 920], [-40, 920],
  ];
  st.reserve(bankPts, '#FCF9EE', 0.96, 1.0);
  st.wash(bankPts, { color: '#A5D462', color2: '#63AB56', alpha: 0.76, layers: 7, variance: 0.06, blur: 0.8, rimStroke: 0.26 });
  // Warm golden sunlit patches across upper meadow
  st.glow(380, 440, 260, 140, '#E8E46E', 0.42, 'multiply');
  st.glow(160, 680, 240, 160, '#4E8F5C', 0.30, 'multiply');

  // Rich hand-painted grass tufts across the bank & softening the water's edge!
  for (let i = 0; i < 32; i++) {
    const gx = st.rng.range(30, 610);
    const gy = st.rng.range(360, 880);
    if (gx + (gy - 360) * 0.44 > 700) continue;
    st.paintGrassTuft(gx, gy, st.rng.range(5, 9), st.rng.range(30, 66), { lean: 0.16, alpha: 0.66, width: 4.2 });
  }
  // Delicate overhanging shoreline grass tufts right where meadow meets creek
  st.paintGrassTuft(655, 455, 8, 52, { lean: 0.35, alpha: 0.72, width: 4.5 });
  st.paintGrassTuft(632, 575, 7, 46, { lean: 0.32, alpha: 0.68, width: 4.2 });
  st.paintGrassTuft(520, 725, 8, 54, { lean: 0.28, alpha: 0.68, width: 4.5 });
  st.paintGrassTuft(410, 835, 9, 60, { lean: 0.24, alpha: 0.70, width: 4.8 });

  // Wet mossy stones along the bank edge
  drawRiverStone(st, 610, 495, 46, 24, { rot: 0.14, moss: true });
  drawRiverStone(st, 550, 635, 58, 26, { rot: -0.08, moss: true });

  // Colorful sunlit spring wildflowers
  const flowers = [
    [145, 560, 1.2, '#FFFFFF', '#FFC53D'], [195, 612, 1.0, '#FFE47A', '#E88E38'],
    [110, 660, 1.05, '#A6D2FF', '#FFE066'], [265, 745, 1.2, '#FFFFFF', '#FFC53D'],
    [455, 540, 0.95, '#FFD1CC', '#FFE066'], [355, 705, 1.0, '#A6D2FF', '#FFE066'],
    [225, 485, 0.95, '#FFFFFF', '#FFC53D'], [88, 760, 1.15, '#FFE47A', '#E88E38'],
  ];
  for (const [fx, fy, fs, fc, cc] of flowers) drawWildflower(st, fx, fy, fs, fc, cc);

  // 6. Storybook Child in sunlit straw sunhat crouching gently by the water's edge!
  drawStorybookChild(st, 465, 475, 1.65);

  // 7. Crisp cream paper boat just released onto the sparkling creek beside the child's fingertips!
  drawPaperBoat(st, 798, 648, 1.28, { tilt: 0.04, sunFromRight: true, withRipples: true });
  st.ripple(798, 660, 175, 30, { alpha: 0.54, thickness: 2.0 });
  st.ripple(802, 664, 245, 42, { alpha: 0.30, thickness: 1.5 });

  // 8. Graceful overhanging willow curtains framing top corners
  drawWillowBranch(st, 1345, -15, 340, -0.18, { alpha: 0.62, blur: 0.6, leafCount: 13 });
  drawWillowBranch(st, 1465, -20, 290, -0.12, { alpha: 0.52, blur: 0.9, leafCount: 11 });
  drawWillowBranch(st, 95, -15, 250, 0.16, { alpha: 0.48, blur: 1.0, leafCount: 9 });

  st.splatter(1160, 465, 180, 16, '#F5BE42', 0.32);
  st.splatter(910, 740, 150, 12, '#55ABC9', 0.28);

  // 9. Optical cold-press paper & wet-bleed watercolor finishing pass!
  st.applyWatercolorPhysics({ warpStrength: 1.35, paperGrain: 0.095, granulation: 0.11, warmth: 0.06 });
}

// ============================================================================
// KEYFRAME 2: 林荫漂流与小停顿 (6–13s)
// Low water-level view into a tranquil shaded bend under overhanging willow trees,
// warm sunlit clearing gleaming ahead on the right!
// ============================================================================
export function renderKF2Eddy(canvas) {
  const st = new WatercolorStudio(canvas, 5022);
  const horizonY = 275;

  // 1. Cool sky left transitioning to warm sunlit golden clearing on far right
  st.paintSky(horizonY, {
    topColor: '#82BFE0',
    midColor: '#C2E4F0',
    horizonColor: '#FFF0C2',
    sunX: 1420,
    sunY: 145,
    sunColor: '#FFE080',
    cloudCount: 2,
  });

  // 2. Distant wooded hills & lush overhanging shady bank trees on the left-center
  st.paintDistantHills(horizonY, [
    { color: '#82B6B0', color2: '#6CA2AE', alpha: 0.48, amp: 52, yOff: -8, freq: 0.0026, phase: 1.2, blur: 3.0 },
    { color: '#5E9E6E', color2: '#468462', alpha: 0.65, amp: 38, yOff: 4, freq: 0.0036, phase: 2.8, blur: 1.8 },
  ]);

  st.paintTree(240, horizonY + 12, 1.35, { sunFromRight: true, alpha: 0.86, blur: 0.9, shadowCol: '#2F6E5C', midCol: '#4F965E' });
  st.paintTree(660, horizonY + 10, 1.15, { sunFromRight: true, alpha: 0.78, blur: 1.2, shadowCol: '#367560', midCol: '#5BA262' });
  st.paintTree(1020, horizonY + 6, 0.85, { sunFromRight: true, alpha: 0.56, blur: 1.8 });

  // 3. Mirror-reflected tranquil shaded turquoise-cobalt creek
  st.paintWaterWithReflection(horizonY, {
    tintTop: '#8BD5DC',
    tintDeep: '#4B9AC0',
    shadeTint: '#4876A8',
    sunX: 1420,
    sunWidth: 280,
    sunColor: '#FFD86B',
    reflectionAlpha: 0.48,
    rippleAmp: 10,
  });

  // Underwater swaying emerald waterweeds
  for (let i = 0; i < 6; i++) {
    const wx = 160 + i * 245 + st.rng.range(-40, 40);
    const wy = st.rng.range(640, 860);
    st.stroke([[wx, wy], [wx + 55, wy - 25], [wx + 125, wy - 12], [wx + 180, wy - 35]], {
      color: '#388568', width: 15, alpha: 0.28, blur: 2.8, rimStroke: 0,
    });
  }

  // 4. Mossy river stones forming the quiet shaded eddy
  drawRiverStone(st, 430, 520, 142, 70, { rot: -0.08, moss: true });
  drawRiverStone(st, 240, 620, 112, 54, { rot: 0.12, moss: true });
  drawRiverStone(st, 585, 585, 52, 25, { rot: 0.15, moss: true });

  st.ripple(725, 580, 165, 32, { alpha: 0.48, shadow: '#3E7EA8', thickness: 1.8 });
  st.ripple(710, 588, 235, 46, { alpha: 0.28, shadow: '#3E7EA8', thickness: 1.5 });

  // 5. Floating willow leaf gently catching the paper boat's bow
  drawFloatingLeaf(st, 625, 562, 1.35, -0.22);

  // 6. Paper boat paused & slightly angled in the cool eddy
  drawPaperBoat(st, 795, 545, 1.48, { tilt: -0.08, sunFromRight: true, withRipples: true, waterTint: '#4B9AC0' });

  // 7. Reeds & hanging willow curtains framing the shaded nook
  drawReedCluster(st, 130, 695, 10, 365, { lean: 0.22, alpha: 0.72, blur: 0.5, width: 12 });
  drawReedCluster(st, 1365, 465, 8, 235, { lean: -0.15, alpha: 0.60, blur: 0.8, width: 9 });
  drawWillowBranch(st, 260, -20, 410, 0.18, { alpha: 0.68, blur: 0.5, leafCount: 15 });
  drawWillowBranch(st, 450, -25, 330, 0.24, { alpha: 0.58, blur: 0.8, leafCount: 12 });
  drawReedCluster(st, 65, 940, 5, 255, { lean: 0.35, colors: ['#3B7E52', '#2E6648'], alpha: 0.52, blur: 3.2, width: 20 });

  st.splatter(690, 640, 180, 14, '#4B9AC0', 0.26);
  st.applyWatercolorPhysics({ warpStrength: 1.35, paperGrain: 0.095, granulation: 0.12, warmth: 0.04 });
}

// ============================================================================
// KEYFRAME 3: 偶遇与轻推 (13–21s) [HERO FRAME]
// Fluffy buttercup duckling emerging from sunlit reeds, tenderly nudging the paper boat's stern
// out of cool turquoise shade into a warm golden diagonal afternoon sunbeam!
// ============================================================================
export function renderKF3Nudge(canvas) {
  const st = new WatercolorStudio(canvas, 5033);
  const horizonY = 290;

  // 1. Sky split: cool fresh turquoise-blue left -> luminous warm peach-gold sun right
  st.paintSky(horizonY, {
    topColor: '#88C9E6',
    midColor: '#CCEBF6',
    horizonColor: '#FFEBB8',
    sunX: 1320,
    sunY: 115,
    sunColor: '#FFD670',
    cloudCount: 3,
  });

  // 2. Distant atmospheric hills & lush sunlit left bank trees
  st.paintDistantHills(horizonY, [
    { color: '#96C4BC', color2: '#82B2BF', alpha: 0.42, amp: 48, yOff: -6, freq: 0.0025, phase: 0.8, blur: 3.0 },
    { color: '#78B674', color2: '#5B9D68', alpha: 0.56, amp: 32, yOff: 4, freq: 0.0038, phase: 2.0, blur: 1.8 },
  ]);
  st.paintTree(210, horizonY + 10, 1.18, { sunFromRight: true, alpha: 0.80, blur: 1.0 });
  st.paintTree(520, horizonY + 6, 0.88, { sunFromRight: true, alpha: 0.62, blur: 1.5 });

  // 3. Mirror-reflected creek transitioning from cool turquoise (left) to glowing golden-aqua (right)!
  st.paintWaterWithReflection(horizonY, {
    tintTop: '#96DCE0',
    tintDeep: '#54AAC8',
    shadeTint: '#4A84B0',
    sunX: 1290,
    sunWidth: 380,
    sunColor: '#FFD666',
    reflectionAlpha: 0.44,
    rippleAmp: 12,
  });

  // Diagonal warm golden afternoon sunbeam slanting down onto the paper boat!
  st.glow(1180, 440, 390, 480, '#FFF2BA', 0.34, 'screen', -0.34);

  // Mossy stone & floating leaf
  drawRiverStone(st, 220, 685, 122, 56, { rot: 0.06, moss: true });
  drawFloatingLeaf(st, 1085, 655, 1.15, 0.18);

  // Fresh green watercolor reeds on the left (where the duckling swam out from)
  drawReedCluster(st, 185, 530, 11, 355, { lean: 0.24, alpha: 0.66, blur: 0.7, width: 12 });
  drawReedCluster(st, 355, 445, 7, 260, { lean: 0.18, alpha: 0.50, blur: 1.2, width: 10 });

  // 4. HERO INTERACTION: Fluffy buttercup duckling gently nudging the paper boat's stern!
  drawFluffyDuckling(st, 646, 578, 2.05, { facingRight: true, headTilt: 0.18, withRipples: true, sunFromRight: true });
  drawPaperBoat(st, 916, 540, 1.62, { tilt: 0.08, sunFromRight: true, withRipples: true, waterTint: '#54AAC8' });

  // Tender nudge-contact micro-ripple & gliding wake
  st.ripple(788, 558, 42, 9, { alpha: 0.80, thickness: 2.0 });
  st.ripple(922, 558, 175, 30, { alpha: 0.52, thickness: 1.9 });
  st.ripple(638, 598, 165, 28, { alpha: 0.44, thickness: 1.7 });

  // 5. Framing willow & soft foreground reeds
  drawWillowBranch(st, 140, -15, 320, 0.20, { alpha: 0.60, blur: 0.8, leafCount: 12 });
  drawReedCluster(st, 75, 935, 6, 285, { lean: 0.30, colors: ['#4A9154', '#38764C'], alpha: 0.50, blur: 3.4, width: 22 });
  drawReedCluster(st, 1525, 945, 4, 215, { lean: -0.25, colors: ['#B0D460', '#74B254'], alpha: 0.42, blur: 3.6, width: 18 });

  st.splatter(1120, 430, 210, 18, '#F5BD44', 0.32);
  st.splatter(480, 660, 160, 12, '#54AAC8', 0.26);

  st.applyWatercolorPhysics({ warpStrength: 1.35, paperGrain: 0.095, granulation: 0.11, warmth: 0.07 });
}

// ============================================================================
// KEYFRAME 4: 驶向阳光 (21–30s) [POETIC FINALE]
// Expansive golden-peach late-afternoon sky, glowing river opening into warm sunlight,
// tiny bright cream boat leaving a shimmering V-wake while the duckling watches peacefully!
// ============================================================================
export function renderKF4Sunlight(canvas) {
  const st = new WatercolorStudio(canvas, 5044);
  const horizonY = 330;

  // 1. Expansive luminous golden-lemon & soft coral-peach afternoon sky
  st.paintSky(horizonY, {
    topColor: '#98D0E8',
    midColor: '#FDE8B6',
    horizonColor: '#FFD6A2',
    sunX: 1185,
    sunY: 185,
    sunColor: '#FFCE68',
    cloudCount: 3,
  });
  st.glow(1340, 160, 360, 220, '#FFB085', 0.34, 'multiply');

  // 2. Soft misty distant hills & golden-lit trees framing the wide glowing river opening
  st.paintDistantHills(horizonY, [
    { color: '#A5C6B8', color2: '#B8B8C8', alpha: 0.38, amp: 52, yOff: -10, freq: 0.0022, phase: 0.4, blur: 3.5 },
    { color: '#8CC07E', color2: '#B8C87A', alpha: 0.48, amp: 28, yOff: 2, freq: 0.0034, phase: 1.9, blur: 2.2 },
  ]);
  st.paintTree(180, horizonY + 8, 1.15, { sunFromRight: true, alpha: 0.72, blur: 1.2 });
  st.paintTree(465, horizonY + 5, 0.78, { sunFromRight: true, alpha: 0.52, blur: 1.8 });
  st.paintTree(1495, horizonY + 6, 0.90, { sunFromRight: true, alpha: 0.56, blur: 1.5, midCol: '#9CC468', lightCol: '#E8DC72' });

  // 3. Expansive shimmering mirror-reflected stream glowing with golden sunlight!
  st.paintWaterWithReflection(horizonY, {
    tintTop: '#A4E0DE',
    tintDeep: '#5FB2CE',
    shadeTint: '#4D8BB8',
    sunX: 1165,
    sunWidth: 440,
    sunColor: '#FFD266',
    reflectionAlpha: 0.48,
    rippleAmp: 13,
  });
  st.glow(1100, 620, 420, 210, '#FFC478', 0.34, 'multiply', 0.04);
  st.glow(280, 720, 390, 210, '#4684AE', 0.28, 'multiply');

  // 4. Delicate undulating white V-wake behind the sailing paper boat
  st.ctx.save();
  st.ctx.globalCompositeOperation = 'screen';
  st.ctx.lineCap = 'round';
  const wake = (pts, bw, ba) => {
    for (let i = 0; i < pts.length - 1; i++) {
      const t = i / (pts.length - 1);
      st.ctx.strokeStyle = `rgba(255,254,248,${ba * (1 - t) * (1 - t * 0.45)})`;
      st.ctx.lineWidth = Math.max(0.8, bw * (1 - t * 0.65));
      st.ctx.beginPath();
      st.ctx.moveTo(pts[i][0], pts[i][1]);
      st.ctx.lineTo(pts[i + 1][0], pts[i + 1][1]);
      st.ctx.stroke();
    }
  };
  wake([[985, 488], [945, 502], [902, 514], [858, 532], [810, 548], [755, 570]], 3.2, 0.80);
  wake([[1012, 492], [982, 512], [952, 534], [918, 558], [882, 584], [842, 614]], 3.0, 0.72);
  st.ctx.restore();
  st.ripple(965, 504, 58, 10, { alpha: 0.48, thickness: 1.5 });
  st.ripple(910, 536, 78, 14, { alpha: 0.30, thickness: 1.2 });

  // 5. Tiny bright cream paper boat sailing into the luminous golden sunlight!
  drawPaperBoat(st, 1025, 475, 0.72, { tilt: -0.03, sunFromRight: true, withRipples: true, waterTint: '#F2CC74' });
  st.glow(1025, 468, 105, 60, '#FFFDF5', 0.54, 'screen');

  // 6. Duckling in foreground left, floating peacefully in soft shade, watching it go
  drawFluffyDuckling(st, 405, 705, 1.32, { facingRight: true, headTilt: -0.08, withRipples: true, sunFromRight: true });

  // Floating poetic afternoon golden bokeh circles in the sunlit air
  for (let i = 0; i < 18; i++) {
    const bx = st.rng.range(760, 1500), by = st.rng.range(85, 420), br = st.rng.range(10, 34);
    st.glow(bx, by, br, br, '#FFFDF4', st.rng.range(0.24, 0.52), 'screen');
  }

  // 7. Framing mossy left bank stone, fresh reeds & overhanging willow
  drawRiverStone(st, 145, 795, 108, 46, { rot: 0.12, moss: true });
  drawReedCluster(st, 110, 910, 10, 365, { lean: 0.25, alpha: 0.64, blur: 1.0, width: 14 });
  drawWillowBranch(st, 180, -15, 350, 0.22, { alpha: 0.58, blur: 0.9, leafCount: 13 });
  drawWillowBranch(st, 340, -20, 270, 0.18, { alpha: 0.48, blur: 1.3, leafCount: 10 });

  st.splatter(1120, 390, 260, 22, '#F5BA45', 0.32);
  st.splatter(350, 760, 150, 12, '#5BB0CE', 0.24);

  st.applyWatercolorPhysics({ warpStrength: 1.35, paperGrain: 0.095, granulation: 0.11, warmth: 0.09 });
}

export const SCENES = {
  kf1_launch: renderKF1Launch,
  kf2_eddy: renderKF2Eddy,
  kf3_nudge: renderKF3Nudge,
  kf4_sunlight: renderKF4Sunlight,
};
