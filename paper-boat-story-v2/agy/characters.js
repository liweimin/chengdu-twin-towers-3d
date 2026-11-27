// characters.js
// Luminous, joyful children's picture-book watercolor characters & botanical props

import { ellipsePoints, sampleBezierShape, sampleCubic } from './watercolor_engine.js';

export const PALETTE = {
  paper: '#FDFBF5',
  // Luminous Watercolor Stream (Cerulean + Turquoise + Sunlit Mint, NEVER muddy grey!)
  waterLight: '#A8E0E0',
  waterMid: '#6BBCD4',
  waterDeep: '#488FB8',
  waterPeriwinkle: '#7D9AC9',
  waterGold: '#FFD666',
  waterPeach: '#FFBE86',
  // Fresh Spring Watercolor Meadow & Foliage
  meadowSun: '#D8E36C',
  meadowLight: '#9FD062',
  meadowMid: '#65AD58',
  meadowDeep: '#3E8457',
  reedSun: '#A3CE63',
  reedMid: '#59A35B',
  reedDeep: '#3A7C55',
  // Origami Paper Boat (Crisp Warm White + Periwinkle Sky Shadow + Warm Gold Bounce)
  boatPaper: '#FFFDF8',
  boatWarm: '#FCECC7',
  boatShade: '#B9D1E6',
  boatCrease: '#7C7066',
  // Fluffy Golden-Buttercup Duckling
  duckLight: '#FFE678',
  duckMid: '#FFC84A',
  duckOchre: '#E89D32',
  duckShade: '#A996B8', // luminous lilac-lavender shadow!
  duckBill: '#F58549',
  duckBillShade: '#D66130',
  duckEye: '#2E1F18',
  // Adorable Storybook Child (Cream shirt + Cornflower-Blue Overalls + Coral Accent)
  skinLight: '#FFE2CC',
  skinShade: '#EEB799',
  cheek: '#F59A92',
  hairMid: '#7D4E35',
  hairLight: '#B5784B',
  hairDeep: '#523020',
  shirtLight: '#FFFDF6',
  shirtShade: '#E0D6C6',
  overallsLight: '#7AAAE0',
  overallsMid: '#5587C4',
  overallsShade: '#42699E',
  hatStraw: '#F6D47A',
  hatRibbon: '#EE7E6C',
  shoeRed: '#D96B59',
  // Delicate Colored-Pencil Linework
  pencilWarm: '#755745',
  pencilBlue: '#4C6E96',
};

function transformPts(pts, cx, cy, scale, rot = 0, flipX = false) {
  const cos = Math.cos(rot), sin = Math.sin(rot);
  const fx = flipX ? -1 : 1;
  return pts.map(([x, y]) => {
    const sx = x * scale * fx;
    const sy = y * scale;
    return [cx + sx * cos - sy * sin, cy + sx * sin + sy * cos];
  });
}

// ============================================================================
// 1. ORIGAMI PAPER BOAT (Crisp paper white + periwinkle sky shadow + sunlit gold bounce)
// ============================================================================
export function drawPaperBoat(wc, cx, cy, scale = 1.0, options = {}) {
  const {
    tilt = 0,
    flipX = false,
    sunFromRight = true,
    withReflection = true,
    withRipples = true,
    waterTint = '#6BBCD4',
  } = options;

  const T = (pts) => transformPts(pts, cx, cy, scale, tilt, flipX);

  if (withReflection) {
    const reflHull = T([[-74, 8], [76, 8], [52, 34], [-48, 34]]);
    const reflSail = T([[-26, 22], [28, 22], [2, 62]]);
    wc.wash(reflHull, {
      color: '#C7E2EA',
      color2: waterTint,
      alpha: 0.36,
      layers: 6,
      variance: 0.14,
      blur: 3.5,
      edgeDarken: 0.05,
      composite: 'multiply',
    });
    wc.wash(reflSail, {
      color: '#E3EEF0',
      alpha: 0.25,
      layers: 5,
      variance: 0.16,
      blur: 4.0,
      edgeDarken: 0.0,
      composite: 'multiply',
    });
    wc.brushStroke(T([[-62, 6], [-20, 9], [20, 9], [64, 5]]), {
      color: '#4682A8',
      width: 8 * scale,
      alpha: 0.38,
      blur: 1.8,
      composite: 'multiply',
    });
  }

  // Crisp reserved paper white base
  const fullSilhouette = T([
    [-82, -16], [-32, -16], [-2, -68], [32, -16], [84, -18], [54, 7], [-50, 7],
  ]);
  wc.gouache(fullSilhouette, PALETTE.boatPaper, 0.96, 0.3);

  // Interior shadow pocket (luminous sky-periwinkle)
  wc.wash(T([[-58, -14], [-22, -16], [24, -16], [60, -15], [32, -2], [-30, -2]]), {
    color: '#A9C4DF',
    color2: '#D5E3EE',
    alpha: 0.44,
    layers: 6,
    variance: 0.04,
    edgeDarken: 0.25,
    blur: 0.6,
    composite: 'multiply',
  });

  // Sail facets (cool periwinkle shade vs warm cream-gold sunlit face)
  wc.wash(T([[-31, -12], [-2, -68], [0, -10]]), {
    color: sunFromRight ? PALETTE.boatShade : PALETTE.boatWarm,
    alpha: sunFromRight ? 0.42 : 0.24,
    layers: 6,
    variance: 0.04,
    edgeDarken: 0.28,
    blur: 0.5,
    composite: 'multiply',
  });
  wc.wash(T([[0, -10], [-2, -68], [32, -12]]), {
    color: sunFromRight ? '#FCEBC4' : PALETTE.boatShade,
    alpha: sunFromRight ? 0.24 : 0.40,
    layers: 6,
    variance: 0.04,
    edgeDarken: 0.20,
    blur: 0.5,
    composite: 'multiply',
  });

  // Front hull facets
  wc.wash(T([[-82, -16], [0, -8], [0, 7], [-50, 7]]), {
    color: sunFromRight ? '#C2D7E8' : '#FBEAC6',
    alpha: sunFromRight ? 0.38 : 0.24,
    layers: 6,
    variance: 0.04,
    edgeDarken: 0.28,
    blur: 0.5,
    composite: 'multiply',
  });
  wc.wash(T([[0, -8], [84, -18], [54, 7], [0, 7]]), {
    color: sunFromRight ? '#FCEBC4' : '#C2D7E8',
    alpha: sunFromRight ? 0.25 : 0.38,
    layers: 6,
    variance: 0.04,
    edgeDarken: 0.22,
    blur: 0.5,
    composite: 'multiply',
  });

  // Crisp sunlit rim highlight
  wc.gouache(T([[-2, -68], [2, -66], [30, -13], [26, -12]]), '#FFFFFF', 0.72, 0.3);
  wc.gouache(T([[6, -8], [82, -17], [78, -13], [6, -5]]), '#FFFFFF', 0.62, 0.3);

  // Delicate colored-pencil fold creases
  const pOpts = { color: '#6E7A8A', width: Math.max(1.0, 1.45 * scale), alpha: 0.52, jitter: 0.45 * scale };
  wc.pencil(T([[-82, -16], [-50, 7], [54, 7], [84, -18]]), pOpts);
  wc.pencil(T([[-82, -16], [0, -8], [84, -18]]), { ...pOpts, alpha: 0.42 });
  wc.pencil(T([[-31, -12], [-2, -68], [32, -12]]), pOpts);
  wc.pencil(T([[-2, -68], [0, -8], [0, 7]]), { ...pOpts, width: Math.max(0.8, 1.1 * scale), alpha: 0.35 });

  if (withRipples) {
    wc.ripple(cx, cy + 7 * scale, 78 * scale, 13 * scale, { alpha: 0.72, thickness: 2.1 * scale });
    wc.ripple(cx + 4 * scale, cy + 9 * scale, 108 * scale, 19 * scale, { alpha: 0.42, thickness: 1.5 * scale });
  }
}

// ============================================================================
// 2. FLUFFY BUTTERCUP-GOLD DUCKLING (luminous yellow + lavender shadow + coral bill)
// ============================================================================
export function drawDuckling(wc, cx, cy, scale = 1.0, options = {}) {
  const {
    facingRight = true,
    headTilt = 0,
    withReflection = true,
    withRipples = true,
    sunFromRight = true,
  } = options;

  const flipX = !facingRight;
  const T = (pts) => transformPts(pts, cx, cy, scale, 0, flipX);
  const TH = (pts) => {
    const cos = Math.cos(headTilt), sin = Math.sin(headTilt);
    const fx = flipX ? -1 : 1;
    return pts.map(([x, y]) => {
      const rx = x - 18, ry = y + 24;
      const nx = 18 + rx * cos - ry * sin;
      const ny = -24 + rx * sin + ry * cos;
      return [cx + nx * scale * fx, cy + ny * scale];
    });
  };

  if (withReflection) {
    wc.wash(T([[-58, 9], [52, 9], [36, 42], [-42, 36]]), {
      color: '#F5CB64',
      color2: '#6FBAD0',
      alpha: 0.34,
      layers: 6,
      variance: 0.16,
      blur: 4.5,
      edgeDarken: 0.0,
      composite: 'multiply',
    });
    wc.brushStroke(T([[-54, 7], [-10, 11], [26, 10], [46, 6]]), {
      color: '#4888AE',
      width: 9 * scale,
      alpha: 0.38,
      blur: 2.0,
      composite: 'multiply',
    });
  }

  // Unified S-curve fluffy silhouette
  const headArc = TH([
    [5, -34], [2, -48], [6, -62], [18, -72], [33, -72], [45, -63], [51, -49], [48, -36], [42, -28],
  ]);
  const bodyArc = T([
    [46, -15], [47, -2], [38, 9], [8, 12], [-28, 11], [-52, 6],
    [-64, -4], [-69, -18], [-62, -23], [-48, -19], [-24, -22], [0, -24],
  ]);
  const unifiedSilhouette = [...headArc, ...bodyArc];

  wc.gouache(unifiedSilhouette, '#FFFDF3', 0.94, 1.0);

  // Luminous sunlit buttercup yellow wash
  wc.wash(unifiedSilhouette, {
    color: PALETTE.duckLight,
    color2: PALETTE.duckMid,
    alpha: 0.84,
    layers: 10,
    variance: 0.07,
    edgeDarken: 0.30,
    granulation: 0.28,
    blur: 1.0,
    composite: 'multiply',
  });

  // Warm honey-ochre & luminous lilac-lavender belly shadow
  wc.wash(T([[-58, -4], [-22, -3], [18, -2], [42, 1], [34, 10], [-14, 12], [-48, 8]]), {
    color: PALETTE.duckOchre,
    color2: PALETTE.duckShade,
    alpha: 0.38,
    layers: 8,
    variance: 0.10,
    blur: 2.4,
    edgeDarken: 0.0,
    composite: 'multiply',
  });

  // Tucked fluffy wing
  wc.wash(T([[-46, -13], [-24, -20], [4, -15], [10, -6], [-4, 1], [-32, 1], [-48, -5]]), {
    color: PALETTE.duckOchre,
    color2: PALETTE.duckMid,
    alpha: 0.38,
    layers: 8,
    variance: 0.08,
    edgeDarken: 0.28,
    blur: 1.2,
    composite: 'multiply',
  });

  if (sunFromRight) {
    wc.gouache(TH(ellipsePoints(36, -58, 12, 9, 12, -0.35)), '#FFFDF6', 0.55, 2.0);
    wc.gouache(T(ellipsePoints(35, -12, 10, 13, 12, 0.2)), '#FFFDF6', 0.45, 2.2);
  }

  // Rosy coral-pink cheek blush
  wc.bloom(TH([[31, -41]])[0][0], TH([[31, -41]])[0][1], 8 * scale, 5.5 * scale, '#F79A92', 0.44, 'multiply');

  // Cute rounded coral-tangerine bill
  const billPts = TH([[47, -47], [58, -46], [69, -42], [72, -38], [67, -34], [55, -34], [45, -36]]);
  wc.gouache(billPts, '#FFE2C8', 0.92, 0.4);
  wc.wash(billPts, {
    color: PALETTE.duckBill,
    color2: PALETTE.duckBillShade,
    alpha: 0.84,
    layers: 6,
    variance: 0.04,
    edgeDarken: 0.30,
    blur: 0.5,
    composite: 'multiply',
  });
  wc.pencil(TH([[47, -40], [58, -39], [68, -39]]), {
    color: '#A84A24',
    width: Math.max(0.85, 1.25 * scale),
    alpha: 0.52,
    jitter: 0.22 * scale,
  });

  // Bright expressive eye + crisp white sparkle
  const eyeCenter = TH([[36, -51]])[0];
  const eyeR = 4.5 * scale;
  wc.ctx.save();
  wc.ctx.fillStyle = PALETTE.duckEye;
  wc.ctx.beginPath();
  wc.ctx.ellipse(eyeCenter[0], eyeCenter[1], eyeR, eyeR * 1.06, 0, 0, Math.PI * 2);
  wc.ctx.fill();
  wc.ctx.fillStyle = '#FFFFFF';
  wc.ctx.beginPath();
  wc.ctx.arc(eyeCenter[0] + (facingRight ? 1.5 : -1.5) * scale, eyeCenter[1] - 1.5 * scale, 1.6 * scale, 0, Math.PI * 2);
  wc.ctx.fill();
  wc.ctx.restore();

  // Delicate colored-pencil accents
  const lp = { color: '#9C6D3B', width: Math.max(0.85, 1.3 * scale), alpha: 0.44, jitter: 0.5 * scale };
  wc.pencil(TH([[5, -58], [16, -71], [34, -72], [46, -62]]), lp);
  wc.pencil(T([[-66, -18], [-48, -19], [-18, -22], [2, -24]]), lp);
  wc.pencil(T([[43, -24], [47, -6], [39, 8]]), { ...lp, alpha: 0.38 });
  wc.pencil(T([[-36, -12], [-12, -18], [8, -11], [-2, -1], [-28, 0]]), { ...lp, alpha: 0.32 });
  wc.pencil(TH([[48, -46], [68, -42], [70, -36], [47, -36]]), { ...lp, color: '#A34F28', alpha: 0.46 });

  if (withRipples) {
    wc.ripple(cx - 2 * scale, cy + 8 * scale, 64 * scale, 12 * scale, { alpha: 0.66, thickness: 1.9 * scale });
    wc.ripple(cx - 12 * scale, cy + 10 * scale, 92 * scale, 17 * scale, { alpha: 0.36, thickness: 1.4 * scale });
  }
}

// ============================================================================
// 3. ADORABLE STORYBOOK CHILD SQUATTING BY THE STREAM BANK (Refined v2)
//    Natural crouching pose, gentle downward gaze at boat, graceful bent elbow,
//    tucked neck under Peter Pan collar, soft fluffy hair with wispy strands
// ============================================================================
export function drawChildByBank(wc, cx, cy, scale = 1.0) {
  const T = (pts) => transformPts(pts, cx, cy, scale, 0, false);

  // Soft ground shadow under squatting feet & hip
  wc.bloom(cx - 8 * scale, cy + 162 * scale, 118 * scale, 26 * scale, '#4E8268', 0.34, 'multiply');

  // 1. Far/back leg & shoe (softer perspective, planted slightly forward)
  const farCalf = T(sampleBezierShape([
    [[34, 82], [50, 88], [56, 114], [48, 142]],
    [[48, 142], [38, 148], [26, 146], [22, 136]],
    [[22, 136], [20, 112], [22, 88], [34, 82]],
  ], 8));
  wc.gouache(farCalf, '#FAECE0', 0.92, 0.3);
  wc.wash(farCalf, { color: PALETTE.skinShade, alpha: 0.65, layers: 5, edgeDarken: 0.20, blur: 0.4 });

  const farShoe = T(sampleBezierShape([
    [[22, 138], [42, 138], [64, 143], [72, 152]],
    [[72, 152], [72, 160], [52, 163], [26, 161]],
    [[26, 161], [18, 158], [16, 146], [22, 138]],
  ], 8));
  wc.gouache(farShoe, '#F5E2D4', 0.92, 0.3);
  wc.wash(farShoe, { color: '#B56350', color2: '#8C4838', alpha: 0.80, layers: 6, edgeDarken: 0.28, blur: 0.4 });

  // 2. Front squatting leg: warm oatmeal-beige shorts + bent knee + bare shin + sock + red Mary-Jane shoe
  const frontShorts = T(sampleBezierShape([
    [[-64, 62], [-22, 42], [20, 38], [40, 56]],
    [[40, 56], [48, 72], [38, 92], [18, 100]],
    [[18, 100], [-14, 112], [-54, 118], [-74, 102]],
    [[-74, 102], [-84, 86], [-78, 68], [-64, 62]],
  ], 10));
  wc.gouache(frontShorts, '#FCF8EE', 0.95, 0.4);
  wc.wash(frontShorts, { color: '#EAD8B4', color2: '#CCB58C', alpha: 0.80, layers: 8, edgeDarken: 0.28, blur: 0.5 });

  // Bare knee & shin curving naturally down-back from knee to ankle
  const frontLeg = T(sampleBezierShape([
    [[22, 64], [38, 66], [42, 82], [28, 106]],
    [[28, 106], [16, 126], [4, 142], [-10, 146]],
    [[-10, 146], [-24, 144], [-26, 132], [-16, 114]],
    [[-16, 114], [-4, 92], [8, 72], [22, 64]],
  ], 10));
  wc.gouache(frontLeg, '#FFF5EC', 0.95, 0.3);
  wc.wash(frontLeg, { color: PALETTE.skinLight, color2: PALETTE.skinShade, alpha: 0.70, layers: 6, edgeDarken: 0.20, blur: 0.4 });

  // Little cream-white ankle sock & rounded coral-red storybook shoe
  const sock = T(sampleBezierShape([
    [[-20, 130], [-4, 128], [4, 138], [2, 150]],
    [[2, 150], [-10, 154], [-24, 150], [-24, 138]],
    [[-24, 138], [-23, 133], [-21, 131], [-20, 130]],
  ], 6));
  wc.gouache(sock, '#FFFDF8', 0.96, 0.3);
  wc.wash(sock, { color: '#EAE3D6', alpha: 0.32, layers: 4, edgeDarken: 0.20 });

  const frontShoe = T(sampleBezierShape([
    [[-26, 144], [-6, 144], [18, 148], [28, 157]],
    [[28, 157], [28, 166], [6, 169], [-20, 167]],
    [[-20, 167], [-32, 163], [-32, 150], [-26, 144]],
  ], 8));
  wc.gouache(frontShoe, '#FCEBE0', 0.95, 0.3);
  wc.wash(frontShoe, { color: PALETTE.shoeRed, color2: '#B54E40', alpha: 0.86, layers: 6, edgeDarken: 0.30, blur: 0.4 });

  // 3. Cozy loose sky-blue cotton smock/tunic (smooth curved back & soft organic watercolor shading)
  const tunic = T(sampleBezierShape([
    [[-8, -50], [14, -50], [34, -36], [40, -10]],
    [[40, -10], [42, 18], [30, 52], [6, 74]],
    [[6, 74], [-26, 86], [-64, 88], [-82, 70]],
    [[-82, 70], [-92, 40], [-78, -4], [-42, -36]],
    [[-42, -36], [-28, -46], [-16, -50], [-8, -50]],
  ], 10));
  wc.gouache(tunic, '#F6FAFE', 0.96, 0.4);
  wc.wash(tunic, {
    color: PALETTE.overallsLight,
    color2: PALETTE.overallsMid,
    alpha: 0.82,
    layers: 10,
    variance: 0.04,
    edgeDarken: 0.30,
    granulation: 0.28,
    blur: 0.6,
  });
  // Soft rounded watercolor shadow along the lower back curve (NO sharp trapezoid!)
  wc.bloom(cx - 56 * scale, cy + 48 * scale, 36 * scale, 32 * scale, PALETTE.overallsShade, 0.34, 'multiply', -0.2);

  // 4. Neck drawn BEFORE collar & extended smoothly up under the jaw (zero gap!)
  const neck = T([[-6, -78], [22, -72], [24, -36], [-8, -38]]);
  wc.gouache(neck, '#FCE9D8', 0.94, 0.3);
  wc.wash(neck, { color: PALETTE.skinShade, alpha: 0.44, layers: 4, blur: 0.6 });

  // Cute rounded cream-white Peter Pan collar sitting neatly ON TOP of neck & shoulders
  const collar = T(sampleBezierShape([
    [[-16, -50], [6, -46], [26, -38], [34, -28]],
    [[34, -28], [20, -20], [-2, -22], [-22, -32]],
    [[-22, -32], [-26, -40], [-22, -48], [-16, -50]],
  ], 8));
  wc.gouache(collar, '#FFFDF7', 0.97, 0.3);
  wc.wash(collar, { color: '#F5ECDA', alpha: 0.38, layers: 4, edgeDarken: 0.24, blur: 0.3 });

  // 5. Front arm with GRACEFUL NATURAL ELBOW BEND!
  //    Upper arm goes DOWN from shoulder (-4, -18) to bent elbow (16, 42),
  //    then forearm reaches gently FORWARD-DOWN to wrist (96, 86) & delicate cupped hand!
  const sleeve = T(sampleBezierShape([
    [[-22, -26], [-2, -30], [16, -18], [22, 6]],
    [[22, 6], [22, 22], [8, 28], [-10, 24]],
    [[-10, 24], [-24, 14], [-30, -2], [-26, -18]],
    [[-26, -18], [-25, -23], [-24, -25], [-22, -26]],
  ], 8));
  wc.gouache(sleeve, '#F6FAFE', 0.96, 0.3);
  wc.wash(sleeve, { color: PALETTE.overallsLight, color2: PALETTE.overallsMid, alpha: 0.80, layers: 6, edgeDarken: 0.28, blur: 0.5 });

  // Natural bent arm (elbow drops down near knee, forearm reaches smoothly forward to boat)
  const bentArmAndHand = T(sampleBezierShape([
    [[14, 14], [22, 28], [28, 40], [34, 46]], // inner elbow bend
    [[34, 46], [56, 62], [78, 74], [98, 82]], // upper forearm to wrist
    [[98, 82], [112, 80], [124, 83], [128, 89]], // delicate thumb
    [[128, 89], [124, 93], [118, 93], [136, 97]], // gentle index finger
    [[136, 97], [142, 102], [136, 107], [126, 107]], // soft fingertips
    [[126, 107], [112, 109], [96, 104], [84, 96]], // soft palm & lower wrist
    [[84, 96], [54, 80], [24, 66], [8, 52]], // lower forearm to outer elbow!
    [[8, 52], [-4, 40], [-6, 26], [-4, 16]], // outer upper arm up into sleeve
    [[-4, 16], [2, 12], [8, 12], [14, 14]],
  ], 8));
  wc.gouache(bentArmAndHand, '#FFF6EE', 0.96, 0.3);
  wc.wash(bentArmAndHand, { color: PALETTE.skinLight, color2: PALETTE.skinShade, alpha: 0.70, layers: 6, edgeDarken: 0.20, blur: 0.4 });

  // 6. Head tilted warmly DOWNWARD (~15 deg) looking tenderly at the paper boat!
  const TH = (pts) => {
    const tilt = 0.22; // gentle downward gaze toward boat
    const cos = Math.cos(tilt), sin = Math.sin(tilt);
    return pts.map(([x, y]) => {
      const rx = x - 14, ry = y + 58;
      const nx = 14 + rx * cos - ry * sin;
      const ny = -58 + rx * sin + ry * cos;
      return [cx + nx * scale, cy + ny * scale];
    });
  };

  const face = TH(sampleBezierShape([
    [[-8, -138], [22, -140], [48, -122], [54, -102]], // soft rounded forehead
    [[54, -102], [58, -94], [63, -89], [57, -83]], // tiny cute button nose
    [[57, -83], [55, -73], [46, -60], [30, -52]], // soft mouth & round chin
    [[30, -52], [8, -48], [-14, -64], [-22, -92]], // chubby cheek & jaw
    [[-22, -92], [-24, -118], [-18, -134], [-8, -138]],
  ], 10));
  wc.gouache(face, '#FFF8F1', 0.97, 0.4);
  wc.wash(face, { color: PALETTE.skinLight, color2: PALETTE.skinShade, alpha: 0.58, layers: 8, edgeDarken: 0.16, blur: 0.5 });

  // Warm rosy peach cheek
  const cheekPt = TH([[34, -77]])[0];
  wc.bloom(cheekPt[0], cheekPt[1], 14 * scale, 10 * scale, PALETTE.cheek, 0.46, 'multiply');

  // Gentle downward-looking smiling eye (expressive dark-brown eye looking toward boat + soft upper lash)
  const eyePt = TH([[42, -94]])[0];
  wc.ctx.save();
  wc.ctx.fillStyle = '#3B251A';
  wc.ctx.beginPath();
  wc.ctx.ellipse(eyePt[0], eyePt[1], 3.7 * scale, 4.2 * scale, 0.25, 0, Math.PI * 2);
  wc.ctx.fill();
  wc.ctx.fillStyle = '#FFFFFF';
  wc.ctx.beginPath();
  wc.ctx.arc(eyePt[0] + 1.1 * scale, eyePt[1] - 1.2 * scale, 1.25 * scale, 0, Math.PI * 2);
  wc.ctx.fill();
  wc.ctx.restore();
  // Soft happy arched eyebrow & sweet gentle smile
  wc.pencil(TH([[32, -104], [41, -109], [49, -105]]), { color: PALETTE.hairMid, width: 1.3 * scale, alpha: 0.48 });
  wc.pencil(TH([[44, -69], [50, -68], [55, -73]]), { color: '#C46C62', width: 1.35 * scale, alpha: 0.70 });

  // 7. Smooth, fluffy chestnut-brown storybook hair (clean natural curve, NO lumpy back bulge!)
  const hair = TH(sampleBezierShape([
    [[-34, -108], [-34, -148], [-2, -168], [34, -162]], // smooth rounded crown
    [[34, -162], [58, -148], [63, -122], [52, -110]], // front bangs
    [[52, -110], [42, -115], [30, -108], [20, -116]], // soft wispy bangs
    [[20, -116], [10, -104], [2, -88], [-4, -64]], // side lock
    [[-4, -64], [-16, -54], [-32, -62], [-38, -82]], // neat soft nape bob
    [[-38, -82], [-40, -96], [-37, -104], [-34, -108]],
  ], 10));
  wc.gouache(hair, '#F2E0CC', 0.80, 0.6);
  wc.wash(hair, {
    color: PALETTE.hairMid,
    color2: PALETTE.hairDeep,
    alpha: 0.86,
    layers: 10,
    variance: 0.06,
    edgeDarken: 0.28,
    granulation: 0.28,
    blur: 0.6,
  });
  // Warm chestnut-gold sunlit highlight on hair (NOT pale white!)
  const hlPt = TH([[14, -142]])[0];
  wc.bloom(hlPt[0], hlPt[1], 28 * scale, 14 * scale, '#D99B5E', 0.38, 'screen', 0.35);

  // Cute little ear peeking neatly through hair
  const earPts = TH(ellipsePoints(0, -86, 6.8, 8.6, 10));
  wc.gouache(earPts, '#FFE4CE', 0.94, 0.3);
  wc.wash(earPts, { color: PALETTE.skinShade, alpha: 0.40, layers: 4 });

  // 8. Clean, accurate colored-pencil contours following outer silhouettes only!
  const lp = { color: PALETTE.pencilWarm, width: 1.35 * scale, alpha: 0.46, jitter: 0.38 * scale };
  const bp = { color: PALETTE.pencilBlue, width: 1.35 * scale, alpha: 0.44, jitter: 0.38 * scale };
  wc.pencil(TH(sampleCubic([50, -106], [56, -94], [63, -89], [57, -83], 8)), lp);
  wc.pencil(TH(sampleCubic([57, -83], [54, -72], [44, -58], [24, -50], 8)), lp);
  wc.pencil(T(sampleCubic([34, -28], [18, -20], [-4, -22], [-22, -32], 8)), { ...lp, alpha: 0.38 });
  wc.pencil(T(sampleCubic([-42, -36], [-78, -4], [-92, 40], [-82, 70], 10)), bp);
  wc.pencil(T(sampleCubic([-82, 70], [-64, 88], [-22, 86], [10, 72], 10)), bp);
  // Bent arm contour tightly hugging inner elbow & outer forearm
  wc.pencil(T(sampleCubic([14, 14], [22, 32], [28, 42], [34, 46], 6)), lp);
  wc.pencil(T(sampleCubic([34, 46], [56, 62], [78, 74], [98, 82], 8)), lp);
  wc.pencil(T(sampleCubic([136, 106], [100, 108], [46, 78], [8, 52], 10)), { ...lp, alpha: 0.38 });
  wc.pencil(T(sampleCubic([8, 52], [-4, 40], [-6, 26], [-4, 16], 6)), { ...lp, alpha: 0.38 });
  // Outer shin & knee contour only (no line cutting across blue tunic!)
  wc.pencil(T(sampleCubic([36, 68], [42, 84], [22, 118], [2, 142], 10)), lp);
}

// ============================================================================
// 4. BOTANICAL & STREAM PROPS (Vibrant Watercolor Leaves, Stones, Wildflowers)
// ============================================================================
export function drawRiverStone(wc, cx, cy, rx, ry, options = {}) {
  const {
    rot = 0,
    color = '#B0ACA0',
    shade = '#7B8CA0', // cool periwinkle-slate shadow instead of muddy grey!
    moss = true,
    inWater = true,
  } = options;

  const stonePts = ellipsePoints(cx, cy, rx, ry, 18, rot);
  wc.gouache(stonePts, '#F8F5EC', 0.88, 0.6);
  wc.wash(stonePts, {
    color,
    color2: shade,
    alpha: 0.72,
    layers: 8,
    variance: 0.08,
    edgeDarken: 0.30,
    granulation: 0.40,
    blur: 0.7,
  });
  if (moss) {
    wc.foliageDabs(cx - rx * 0.06, cy - ry * 0.25, rx * 0.56, ry * 0.36, 12,
      [PALETTE.meadowSun, PALETTE.meadowLight, PALETTE.meadowMid],
      { dabMin: rx * 0.14, dabMax: rx * 0.28, alpha: 0.62, blur: 0.6, edgeDarken: 0.32 }
    );
  }
  wc.pencil(stonePts.slice(0, 9), { color: '#64707E', width: 1.1, alpha: 0.34, jitter: 0.5 });
  if (inWater) {
    wc.ripple(cx, cy + ry * 0.75, rx * 1.16, ry * 0.34, { alpha: 0.54, thickness: 1.7 });
  }
}

export function drawFloatingLeaf(wc, cx, cy, scale = 1.0, rot = -0.2) {
  const T = (pts) => transformPts(pts, cx, cy, scale, rot, false);
  const leafPts = T([[-44, 0], [-18, -11], [14, -9], [46, 0], [14, 10], [-18, 11]]);
  wc.wash(T([[-40, 4], [42, 4], [18, 14], [-20, 14]]), {
    color: '#4E8AA8',
    alpha: 0.32,
    layers: 4,
    blur: 2.0,
    edgeDarken: 0.0,
  });
  wc.gouache(leafPts, '#FAF6D8', 0.90, 0.3);
  wc.wash(leafPts, {
    color: '#C7DC5E',
    color2: '#6FB054',
    alpha: 0.82,
    layers: 6,
    variance: 0.06,
    edgeDarken: 0.34,
    blur: 0.4,
  });
  wc.pencil(T([[-42, 0], [0, -1], [44, 0]]), { color: '#4E7D44', width: 1.1 * scale, alpha: 0.55 });
  wc.ripple(cx, cy + 4 * scale, 52 * scale, 11 * scale, { alpha: 0.48, thickness: 1.4 * scale });
}

export function drawReedCluster(wc, baseX, baseY, count = 7, height = 280, options = {}) {
  const {
    lean = 0.2,
    color = PALETTE.reedSun,
    color2 = PALETTE.reedMid,
    alpha = 0.65,
    blur = 0.5,
    width = 10,
  } = options;

  for (let i = 0; i < count; i++) {
    const x0 = baseX + wc.rng.range(-55, 55);
    const h = height * wc.rng.range(0.65, 1.15);
    const bend = (lean + wc.rng.range(-0.20, 0.20)) * h;
    const pts = [
      [x0, baseY],
      [x0 + bend * 0.25, baseY - h * 0.33],
      [x0 + bend * 0.62, baseY - h * 0.68],
      [x0 + bend, baseY - h],
    ];
    wc.brushStroke(pts, {
      color: i % 2 === 0 ? color : color2,
      width: width * wc.rng.range(0.7, 1.25),
      alpha: alpha * wc.rng.range(0.75, 1.1),
      blur,
      taperStart: 0.6,
      taperEnd: 0.02,
      dryness: 0.22,
    });
  }
}

export function drawWillowBranch(wc, startX, startY, length = 320, droop = 0.35, options = {}) {
  const {
    color = '#87BE5D',
    color2 = '#559C54',
    alpha = 0.60,
    blur = 0.6,
    leafCount = 13,
  } = options;

  const endX = startX + length * droop;
  const endY = startY + length;
  const midX = (startX + endX) * 0.5 + wc.rng.range(-16, 16);
  const midY = (startY + endY) * 0.5;

  wc.pencil([[startX, startY], [midX, midY], [endX, endY]], {
    color: '#5B804B',
    width: 1.3,
    alpha: alpha * 0.72,
    jitter: 0.4,
  });

  for (let i = 1; i <= leafCount; i++) {
    const t = i / (leafCount + 1);
    const lx = (1 - t) * (1 - t) * startX + 2 * (1 - t) * t * midX + t * t * endX;
    const ly = (1 - t) * (1 - t) * startY + 2 * (1 - t) * t * midY + t * t * endY;
    const side = i % 2 === 0 ? 1 : -1;
    const leafLen = wc.rng.range(28, 48);
    const ang = Math.PI * 0.5 + side * wc.rng.range(0.32, 0.72);
    wc.brushStroke([
      [lx, ly],
      [lx + Math.cos(ang) * leafLen * 0.5, ly + Math.sin(ang) * leafLen * 0.5],
      [lx + Math.cos(ang) * leafLen, ly + Math.sin(ang) * leafLen],
    ], {
      color: i % 3 === 0 ? color2 : color,
      width: wc.rng.range(9, 14),
      alpha: alpha * wc.rng.range(0.75, 1.1),
      blur,
      taperStart: 0.15,
      taperEnd: 0.05,
    });
  }
}

export function drawWildflower(wc, cx, cy, scale = 1.0, petalColor = '#FFFDF5', centerColor = '#FFC640') {
  for (let i = 0; i < 5; i++) {
    const a = (i / 5) * Math.PI * 2 + wc.rng.range(-0.15, 0.15);
    const px = cx + Math.cos(a) * 6.8 * scale;
    const py = cy + Math.sin(a) * 6.8 * scale;
    wc.gouache(ellipsePoints(px, py, 5.2 * scale, 3.8 * scale, 8, a), petalColor, 0.92, 0.3);
  }
  wc.gouache(ellipsePoints(cx, cy, 3.6 * scale, 3.6 * scale, 8), centerColor, 0.95, 0.2);
}

export function drawWaterSparkles(wc, x1, y1, x2, y2, count = 48, maxRx = 18) {
  for (let i = 0; i < count; i++) {
    const t = wc.rng.next();
    const x = x1 + (x2 - x1) * t + wc.rng.gauss(0, (x2 - x1) * 0.14);
    const y = y1 + (y2 - y1) * wc.rng.next();
    const rx = wc.rng.range(3, maxRx);
    const ry = rx * wc.rng.range(0.18, 0.38);
    wc.gouache(ellipsePoints(x, y, rx, ry, 10), '#FFFFFF', wc.rng.range(0.50, 0.92), wc.rng.range(0.3, 1.6));
  }
}
