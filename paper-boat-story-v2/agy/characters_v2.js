// characters_v2.js
// Rich, volumetric, Ghibli / classic European picture-book watercolor characters & props

import { ellipsePts, sampleBezierShape, sampleCubic } from './watercolor_v2.js';

export const PAL = {
  // Paper Boat
  boatPaper: '#FFFDF8',
  boatWarm: '#FCEBC4',
  boatShade: '#A9C6E0',
  boatCrease: '#64768C',
  // Duckling
  duckSun: '#FFF099',
  duckMid: '#FFC94B',
  duckOchre: '#E59630',
  duckShadow: '#9B8AB2',
  duckBill: '#F27D42',
  duckBillDeep: '#C95424',
  // Child
  skinLight: '#FFE4CE',
  skinShade: '#E8B092',
  cheek: '#F5928B',
  hairMid: '#7A4A32',
  hairDeep: '#4D2B1B',
  hatLight: '#FCE293',
  hatMid: '#E6B856',
  hatShade: '#B8893A',
  ribbon: '#E36B5B',
  ribbonDeep: '#B34638',
  tunicLight: '#82B5E6',
  tunicMid: '#588DC9',
  tunicShade: '#3E6599',
  shortsLight: '#F0DEC0',
  shortsShade: '#C7AF88',
  shoe: '#C95F4C',
  shoeDeep: '#963E30',
  // Pencil
  sepia: '#6E5140',
  indigo: '#45648A',
};

function xform(pts, cx, cy, scale, rot = 0, flipX = false) {
  const cos = Math.cos(rot), sin = Math.sin(rot), fx = flipX ? -1 : 1;
  return pts.map(([x, y]) => {
    const sx = x * scale * fx, sy = y * scale;
    return [cx + sx * cos - sy * sin, cy + sx * sin + sy * cos];
  });
}

// ============================================================================
// 1. ORIGAMI PAPER BOAT (Volumetric folds + cool sky shadow + warm water reflection)
// ============================================================================
export function drawPaperBoat(st, cx, cy, scale = 1.0, opts = {}) {
  const { tilt = 0, flipX = false, sunFromRight = true, withRipples = true, waterTint = '#5CAEC9' } = opts;
  const T = (pts) => xform(pts, cx, cy, scale, tilt, flipX);

  // Rippled mirror reflection beneath boat
  st.wash(T([[-72, 9], [74, 9], [52, 36], [-48, 36]]), {
    color: '#D5E9EE', color2: waterTint, alpha: 0.40, layers: 5, variance: 0.14, blur: 3.5, rimStroke: 0,
  });
  st.wash(T([[-26, 22], [28, 22], [2, 64]]), {
    color: '#E6F1F2', alpha: 0.26, layers: 4, variance: 0.16, blur: 4.5, rimStroke: 0,
  });
  st.stroke(T([[-62, 6], [-20, 9], [20, 9], [64, 5]]), {
    color: '#3B789E', width: 8 * scale, alpha: 0.42, blur: 1.8, rimStroke: 0,
  });

  // Crisp paper-white base
  st.reserve(T([[-82, -16], [-32, -16], [-2, -68], [32, -16], [84, -18], [54, 7], [-50, 7]]), PAL.boatPaper, 0.97, 0.3);

  // Interior shadow pocket
  st.wash(T([[-58, -14], [-22, -16], [24, -16], [60, -15], [32, -2], [-30, -2]]), {
    color: '#9DBCD9', color2: '#C8DCEB', alpha: 0.46, layers: 5, variance: 0.04, blur: 0.5, rimStroke: 0.18,
  });

  // Sail facets (cool periwinkle shade vs warm golden sunlit paper)
  st.wash(T([[-31, -12], [-2, -68], [0, -10]]), {
    color: sunFromRight ? PAL.boatShade : PAL.boatWarm,
    alpha: sunFromRight ? 0.45 : 0.24, layers: 5, variance: 0.04, blur: 0.4, rimStroke: 0.20,
  });
  st.wash(T([[0, -10], [-2, -68], [32, -12]]), {
    color: sunFromRight ? '#FDECC2' : PAL.boatShade,
    alpha: sunFromRight ? 0.25 : 0.42, layers: 5, variance: 0.04, blur: 0.4, rimStroke: 0.14,
  });

  // Hull facets + subtle turquoise water bounce on lower hull
  st.wash(T([[-82, -16], [0, -8], [0, 7], [-50, 7]]), {
    color: sunFromRight ? '#B6D0E3' : '#FBEAC6',
    alpha: sunFromRight ? 0.42 : 0.24, layers: 5, variance: 0.04, blur: 0.4, rimStroke: 0.20,
  });
  st.wash(T([[0, -8], [84, -18], [54, 7], [0, 7]]), {
    color: sunFromRight ? '#FCEBC4' : '#B6D0E3',
    alpha: sunFromRight ? 0.26 : 0.40, layers: 5, variance: 0.04, blur: 0.4, rimStroke: 0.15,
  });

  // Crisp sunlit rim highlights
  st.reserve(T([[-2, -68], [2, -66], [30, -13], [26, -12]]), '#FFFFFF', 0.78, 0.3);
  st.reserve(T([[6, -8], [82, -17], [78, -13], [6, -5]]), '#FFFFFF', 0.65, 0.3);

  // Delicate colored-pencil fold creases
  const p = { color: PAL.boatCrease, width: Math.max(0.95, 1.4 * scale), alpha: 0.56, jitter: 0.4 * scale };
  st.pencil(T([[-82, -16], [-50, 7], [54, 7], [84, -18]]), p);
  st.pencil(T([[-82, -16], [0, -8], [84, -18]]), { ...p, alpha: 0.44 });
  st.pencil(T([[-31, -12], [-2, -68], [32, -12]]), p);
  st.pencil(T([[-2, -68], [0, -8], [0, 7]]), { ...p, width: Math.max(0.8, 1.05 * scale), alpha: 0.36 });

  if (withRipples) {
    st.ripple(cx, cy + 7 * scale, 78 * scale, 13 * scale, { alpha: 0.75, thickness: 2.0 * scale });
    st.ripple(cx + 4 * scale, cy + 9 * scale, 112 * scale, 19 * scale, { alpha: 0.42, thickness: 1.5 * scale });
  }
}

// ============================================================================
// 2. FLUFFY PAINTERLY WATERCOLOR DUCKLING (Feathery down tufts + 3-value shading!)
// ============================================================================
export function drawFluffyDuckling(st, cx, cy, scale = 1.0, opts = {}) {
  const { facingRight = true, headTilt = 0, withRipples = true, sunFromRight = true } = opts;
  const flipX = !facingRight;
  const T = (pts) => xform(pts, cx, cy, scale, 0, flipX);
  const TH = (pts) => {
    const cos = Math.cos(headTilt), sin = Math.sin(headTilt), fx = flipX ? -1 : 1;
    return pts.map(([x, y]) => {
      const rx = x - 18, ry = y + 24;
      return [cx + (18 + rx * cos - ry * sin) * scale * fx, cy + (-24 + rx * sin + ry * cos) * scale];
    });
  };

  // Water reflection & contact shadow
  st.wash(T([[-58, 9], [52, 9], [36, 44], [-42, 38]]), {
    color: '#F5CA60', color2: '#5CB2CC', alpha: 0.36, layers: 5, variance: 0.16, blur: 4.5, rimStroke: 0,
  });
  st.stroke(T([[-54, 7], [-10, 11], [26, 10], [46, 6]]), {
    color: '#3B7DA4', width: 9 * scale, alpha: 0.42, blur: 2.0, rimStroke: 0,
  });

  // Unified fluffy S-curve silhouette
  const headArc = TH([
    [5, -34], [2, -48], [6, -62], [18, -72], [33, -72], [45, -63], [51, -49], [48, -36], [42, -28],
  ]);
  const bodyArc = T([
    [46, -15], [47, -2], [38, 9], [8, 12], [-28, 11], [-52, 6],
    [-64, -4], [-70, -19], [-62, -24], [-48, -19], [-24, -22], [0, -24],
  ]);
  const sil = [...headArc, ...bodyArc];

  st.reserve(sil, '#FFFDF3', 0.96, 1.0);

  // Value 1: Luminous buttercup-gold wash
  st.wash(sil, {
    color: PAL.duckSun, color2: PAL.duckMid, alpha: 0.86, layers: 8, variance: 0.06, blur: 0.9, rimStroke: 0.24,
  });

  // Value 2: Warm honey-ochre & luminous lilac-lavender belly/underwing shadow
  st.wash(T([[-58, -4], [-22, -3], [18, -2], [42, 1], [34, 10], [-14, 12], [-48, 8]]), {
    color: PAL.duckOchre, color2: PAL.duckShadow, alpha: 0.42, layers: 6, variance: 0.10, blur: 2.4, rimStroke: 0,
  });
  // Soft nape shading
  st.wash(TH([[2, -48], [10, -66], [24, -70], [14, -50], [8, -30], [1, -32]]), {
    color: PAL.duckOchre, alpha: 0.28, layers: 5, blur: 2.2, rimStroke: 0,
  });

  // Soft tucked fluffy wing
  st.wash(T([[-46, -13], [-24, -20], [4, -15], [10, -6], [-4, 1], [-32, 1], [-48, -5]]), {
    color: PAL.duckOchre, color2: PAL.duckMid, alpha: 0.42, layers: 6, variance: 0.08, blur: 1.0, rimStroke: 0.22,
  });

  // Feathery soft down tufts along crown, chest, back & tail (makes it look genuinely plush!)
  const tufts = [
    TH([[16, -71], [12, -77]]), TH([[22, -72], [20, -78]]), TH([[29, -71], [29, -76]]),
    T([[-66, -18], [-73, -24]]), T([[-62, -21], [-68, -27]]),
    T([[44, -14], [49, -12]]), T([[46, -6], [51, -4]]),
  ];
  for (const tf of tufts) {
    st.stroke(tf, { color: PAL.duckMid, width: 4.5 * scale, alpha: 0.65, blur: 0.5, rimStroke: 0 });
  }

  // Sunlit cream-gold rim light on forehead, back & chest
  if (sunFromRight) {
    const h1 = TH([[37, -58]])[0];
    st.glow(h1[0], h1[1], 14 * scale, 10 * scale, '#FFFDF6', 0.62, 'screen', -0.3);
    const h2 = T([[35, -12]])[0];
    st.glow(h2[0], h2[1], 12 * scale, 14 * scale, '#FFFDF6', 0.50, 'screen', 0.2);
  }

  // Rosy coral cheek blush
  const ck = TH([[31, -41]])[0];
  st.glow(ck[0], ck[1], 9 * scale, 6 * scale, '#F7928A', 0.48, 'multiply');

  // Cute rounded translucent coral-tangerine bill with highlight & smile line
  const bill = TH([[47, -47], [58, -46], [69, -42], [72, -38], [67, -34], [55, -34], [45, -36]]);
  st.reserve(bill, '#FFE2C8', 0.94, 0.3);
  st.wash(bill, { color: PAL.duckBill, color2: PAL.duckBillDeep, alpha: 0.86, layers: 5, variance: 0.04, blur: 0.4, rimStroke: 0.26 });
  st.reserve(TH(ellipsePts(57, -44, 5.5, 1.8, 8, 0.1)), '#FFF4E6', 0.55, 0.4);
  st.pencil(TH([[47, -40], [58, -39], [68, -39]]), { color: '#9E421E', width: Math.max(0.85, 1.2 * scale), alpha: 0.55 });

  // Expressive glossy dark-brown eye + sky reflection + crisp white catchlight
  const eye = TH([[36, -51]])[0];
  const er = 4.6 * scale;
  st.ctx.save();
  st.ctx.fillStyle = '#2B1B14';
  st.ctx.beginPath();
  st.ctx.ellipse(eye[0], eye[1], er, er * 1.06, 0, 0, Math.PI * 2);
  st.ctx.fill();
  // Subtle lower sky-blue iris bounce
  st.ctx.fillStyle = 'rgba(130, 195, 225, 0.45)';
  st.ctx.beginPath();
  st.ctx.arc(eye[0] - (facingRight ? 0.8 : -0.8) * scale, eye[1] + 1.6 * scale, 1.8 * scale, 0, Math.PI * 2);
  st.ctx.fill();
  // Crisp white catchlight
  st.ctx.fillStyle = '#FFFFFF';
  st.ctx.beginPath();
  st.ctx.arc(eye[0] + (facingRight ? 1.5 : -1.5) * scale, eye[1] - 1.5 * scale, 1.65 * scale, 0, Math.PI * 2);
  st.ctx.fill();
  st.ctx.restore();

  // Delicate colored-pencil accents
  const lp = { color: '#946535', width: Math.max(0.85, 1.25 * scale), alpha: 0.42, jitter: 0.45 * scale };
  st.pencil(TH([[5, -58], [16, -71], [34, -72], [46, -62]]), lp);
  st.pencil(T([[-66, -18], [-48, -19], [-18, -22], [2, -24]]), lp);
  st.pencil(T([[43, -24], [47, -6], [39, 8]]), { ...lp, alpha: 0.36 });
  st.pencil(T([[-36, -12], [-12, -18], [8, -11], [-2, -1], [-28, 0]]), { ...lp, alpha: 0.30 });
  st.pencil(TH([[48, -46], [68, -42], [70, -36], [47, -36]]), { ...lp, color: '#9E4B24', alpha: 0.46 });

  if (withRipples) {
    st.ripple(cx - 2 * scale, cy + 8 * scale, 64 * scale, 12 * scale, { alpha: 0.68, thickness: 1.9 * scale });
    st.ripple(cx - 12 * scale, cy + 10 * scale, 94 * scale, 17 * scale, { alpha: 0.38, thickness: 1.4 * scale });
  }
}

// ============================================================================
// 3. MIYAZAKI / STORYBOOK WATERCOLOR CHILD CROUCHING BY THE STREAM BANK
//    Poetic 3/4 rear-side crouching pose in a sunlit straw sunhat with coral ribbon bow,
//    fluffy chestnut hair locks peeking under the brim, rosy 3/4 cheek, draped sky-blue smock,
//    natural bent elbow & delicate reaching hand!
// ============================================================================
export function drawStorybookChild(st, cx, cy, scale = 1.0) {
  const T = (pts) => xform(pts, cx, cy, scale, 0, false);

  // Soft dappled meadow ground shadow under crouching child
  st.glow(cx - 8 * scale, cy + 162 * scale, 124 * scale, 28 * scale, '#3E7858', 0.40, 'multiply');

  // 1. Far crouching leg & shoe (planted slightly forward for balance)
  const farCalf = T(sampleBezierShape([
    [[34, 82], [50, 88], [56, 114], [48, 142]],
    [[48, 142], [38, 148], [26, 146], [22, 136]],
    [[22, 136], [20, 112], [22, 88], [34, 82]],
  ], 8));
  st.reserve(farCalf, '#FAECE0', 0.94, 0.3);
  st.wash(farCalf, { color: PAL.skinShade, alpha: 0.64, layers: 4, blur: 0.4, rimStroke: 0.16 });

  const farShoe = T(sampleBezierShape([
    [[22, 138], [42, 138], [64, 143], [72, 152]],
    [[72, 152], [72, 160], [52, 163], [26, 161]],
    [[26, 161], [18, 158], [16, 146], [22, 138]],
  ], 8));
  st.reserve(farShoe, '#F5E2D4', 0.94, 0.3);
  st.wash(farShoe, { color: '#B56350', color2: '#8C4838', alpha: 0.84, layers: 5, blur: 0.4, rimStroke: 0.24 });

  // 2. Front squatting leg: oatmeal linen shorts + bare knee & shin + white sock + red shoe
  const shorts = T(sampleBezierShape([
    [[-64, 62], [-22, 42], [20, 38], [40, 56]],
    [[40, 56], [48, 72], [38, 92], [18, 100]],
    [[18, 100], [-14, 112], [-54, 118], [-74, 102]],
    [[-74, 102], [-84, 86], [-78, 68], [-64, 62]],
  ], 10));
  st.reserve(shorts, '#FCF8EE', 0.96, 0.3);
  st.wash(shorts, { color: PAL.shortsLight, color2: PAL.shortsShade, alpha: 0.82, layers: 6, blur: 0.5, rimStroke: 0.24 });

  const frontLeg = T(sampleBezierShape([
    [[22, 64], [38, 66], [42, 82], [28, 106]],
    [[28, 106], [16, 126], [4, 142], [-10, 146]],
    [[-10, 146], [-24, 144], [-26, 132], [-16, 114]],
    [[-16, 114], [-4, 92], [8, 72], [22, 64]],
  ], 10));
  st.reserve(frontLeg, '#FFF5EC', 0.96, 0.3);
  st.wash(frontLeg, { color: PAL.skinLight, color2: PAL.skinShade, alpha: 0.70, layers: 5, blur: 0.4, rimStroke: 0.18 });

  const sock = T(sampleBezierShape([
    [[-20, 130], [-4, 128], [4, 138], [2, 150]],
    [[2, 150], [-10, 154], [-24, 150], [-24, 138]],
    [[-24, 138], [-23, 133], [-21, 131], [-20, 130]],
  ], 6));
  st.reserve(sock, '#FFFDF8', 0.97, 0.3);
  st.wash(sock, { color: '#E8E0D2', alpha: 0.32, layers: 3, rimStroke: 0.16 });

  const frontShoe = T(sampleBezierShape([
    [[-26, 144], [-6, 144], [18, 148], [28, 157]],
    [[28, 157], [28, 166], [6, 169], [-20, 167]],
    [[-20, 167], [-32, 163], [-32, 150], [-26, 144]],
  ], 8));
  st.reserve(frontShoe, '#FCEBE0', 0.96, 0.3);
  st.wash(frontShoe, { color: PAL.shoe, color2: PAL.shoeDeep, alpha: 0.88, layers: 5, blur: 0.4, rimStroke: 0.26 });

  // 3. Cozy draped sky-blue linen smock (3-value watercolor folds + sunlit shoulder highlight!)
  const tunic = T(sampleBezierShape([
    [[-10, -50], [14, -50], [34, -36], [40, -10]],
    [[40, -10], [42, 18], [30, 52], [6, 74]],
    [[6, 74], [-26, 86], [-64, 88], [-84, 70]],
    [[-84, 70], [-94, 40], [-78, -4], [-42, -36]],
    [[-42, -36], [-28, -46], [-16, -50], [-10, -50]],
  ], 10));
  st.reserve(tunic, '#F6FAFE', 0.97, 0.4);
  st.wash(tunic, { color: PAL.tunicLight, color2: PAL.tunicMid, alpha: 0.82, layers: 8, variance: 0.04, blur: 0.6, rimStroke: 0.26 });
  // Soft volumetric shadow folds along lower back
  st.glow(cx - 56 * scale, cy + 48 * scale, 40 * scale, 34 * scale, PAL.tunicShade, 0.38, 'multiply', -0.2);
  st.stroke(T([[-54, -18], [-64, 24], [-60, 74]]), { color: PAL.tunicShade, width: 10 * scale, alpha: 0.26, blur: 2.2, rimStroke: 0 });
  st.stroke(T([[-26, -12], [-34, 30], [-28, 78]]), { color: PAL.tunicShade, width: 9 * scale, alpha: 0.22, blur: 2.2, rimStroke: 0 });
  // Sunlit cream rim highlight on chest/front shoulder
  st.glow(cx + 22 * scale, cy - 16 * scale, 22 * scale, 28 * scale, '#FFFDF4', 0.36, 'screen');

  // Soft neck tucked under Peter Pan collar
  const neck = T([[-6, -78], [22, -72], [24, -36], [-8, -38]]);
  st.reserve(neck, '#FCE9D8', 0.95, 0.3);
  st.wash(neck, { color: PAL.skinShade, alpha: 0.44, layers: 4, blur: 0.6, rimStroke: 0 });

  // Cream-white Peter Pan collar
  const collar = T(sampleBezierShape([
    [[-18, -50], [6, -46], [26, -38], [34, -28]],
    [[34, -28], [20, -20], [-2, -22], [-24, -32]],
    [[-24, -32], [-28, -40], [-24, -48], [-18, -50]],
  ], 8));
  st.reserve(collar, '#FFFDF7', 0.98, 0.3);
  st.wash(collar, { color: '#F2E7D2', alpha: 0.38, layers: 4, blur: 0.3, rimStroke: 0.22 });

  // 4. Natural bent reaching arm & delicate small hand
  const sleeve = T(sampleBezierShape([
    [[-22, -26], [-2, -30], [16, -18], [22, 6]],
    [[22, 6], [22, 22], [8, 28], [-10, 24]],
    [[-10, 24], [-24, 14], [-30, -2], [-26, -18]],
    [[-26, -18], [-25, -23], [-24, -25], [-22, -26]],
  ], 8));
  st.reserve(sleeve, '#F6FAFE', 0.97, 0.3);
  st.wash(sleeve, { color: PAL.tunicLight, color2: PAL.tunicMid, alpha: 0.80, layers: 5, blur: 0.4, rimStroke: 0.24 });

  const armAndHand = T(sampleBezierShape([
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
  st.reserve(armAndHand, '#FFF6EE', 0.97, 0.3);
  st.wash(armAndHand, { color: PAL.skinLight, color2: PAL.skinShade, alpha: 0.70, layers: 5, blur: 0.4, rimStroke: 0.18 });

  // 5. Tilted Head + Rosy 3/4 Cheek + Fluffy Hair + SUNLIT WOVEN STRAW SUNHAT WITH CORAL RIBBON!
  const TH = (pts) => {
    const tilt = 0.26; // tender downward gaze at the paper boat
    const cos = Math.cos(tilt), sin = Math.sin(tilt);
    return pts.map(([x, y]) => {
      const rx = x - 14, ry = y + 58;
      return [cx + (14 + rx * cos - ry * sin) * scale, cy + (-58 + rx * sin + ry * cos) * scale];
    });
  };

  // Under-brim back of straw hat (behind head/hair)
  const hatBackBrim = TH(ellipsePts(10, -124, 72, 24, 22, -0.06));
  st.reserve(hatBackBrim, '#F9E7B6', 0.92, 0.5);
  st.wash(hatBackBrim, { color: PAL.hatMid, color2: PAL.hatShade, alpha: 0.78, layers: 5, blur: 0.5, rimStroke: 0.26 });

  // Soft rounded toddler face peeking warmly under the straw hat brim
  const face = TH(sampleBezierShape([
    [[-8, -132], [22, -134], [46, -118], [52, -100]],
    [[52, -100], [56, -92], [60, -87], [55, -82]],
    [[55, -82], [53, -72], [44, -60], [28, -52]],
    [[28, -52], [8, -48], [-14, -64], [-22, -92]],
    [[-22, -92], [-24, -114], [-18, -128], [-8, -132]],
  ], 10));
  st.reserve(face, '#FFF8F1', 0.98, 0.3);
  st.wash(face, { color: PAL.skinLight, color2: PAL.skinShade, alpha: 0.58, layers: 6, blur: 0.4, rimStroke: 0.14 });
  // Soft cool hat-brim shadow across upper forehead
  st.glow(TH([[26, -114]])[0][0], TH([[26, -114]])[0][1], 32 * scale, 12 * scale, '#9AA8C4', 0.28, 'multiply', 0.15);

  // Rosy peach cheek & gentle smiling downward-curved happy eye!
  const ckPt = TH([[34, -77]])[0];
  st.glow(ckPt[0], ckPt[1], 14 * scale, 10 * scale, PAL.cheek, 0.48, 'multiply');

  const eyePt = TH([[41, -93]])[0];
  st.ctx.save();
  st.ctx.strokeStyle = '#4A2B1D';
  st.ctx.lineWidth = 2.4 * scale;
  st.ctx.lineCap = 'round';
  st.ctx.beginPath();
  // Sweet, serene happy downward-curved storybook lash looking down at the boat!
  st.ctx.arc(eyePt[0], eyePt[1] - 1.5 * scale, 4.8 * scale, 0.18 * Math.PI, 0.88 * Math.PI);
  st.ctx.stroke();
  st.ctx.restore();
  st.pencil(TH([[43, -69], [49, -68], [54, -72]]), { color: '#C4685E', width: 1.35 * scale, alpha: 0.72 });

  // Soft fluffy chestnut hair locks peeking out from under the straw hat!
  const hairUnder = TH(sampleBezierShape([
    [[-34, -116], [-10, -124], [24, -122], [46, -112]],
    [[46, -112], [32, -108], [16, -110], [4, -92]],
    [[4, -92], [-2, -74], [-14, -56], [-32, -62]],
    [[-32, -62], [-42, -78], [-42, -100], [-34, -116]],
  ], 10));
  st.reserve(hairUnder, '#EBD6C0', 0.90, 0.5);
  st.wash(hairUnder, { color: PAL.hairMid, color2: PAL.hairDeep, alpha: 0.86, layers: 7, variance: 0.06, blur: 0.6, rimStroke: 0.24 });

  // Cute small ear peeking through hair
  const ear = TH(ellipsePts(1, -86, 6.6, 8.4, 10));
  st.reserve(ear, '#FFE4CE', 0.95, 0.3);
  st.wash(ear, { color: PAL.skinShade, alpha: 0.40, layers: 3, rimStroke: 0 });

  // SUNLIT WOVEN STRAW SUNHAT (Crown + Front Brim + Coral Ribbon Bow & Fluttering Tails!)
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
  st.reserve(hatCrown, '#FFF8E2', 0.96, 0.4);
  st.wash(hatCrown, { color: PAL.hatLight, color2: PAL.hatMid, alpha: 0.86, layers: 7, variance: 0.05, blur: 0.5, rimStroke: 0.28 });
  st.reserve(hatFrontBrim, '#FFF9E8', 0.96, 0.4);
  st.wash(hatFrontBrim, { color: PAL.hatLight, color2: PAL.hatMid, alpha: 0.80, layers: 6, variance: 0.05, blur: 0.5, rimStroke: 0.26 });
  // Sunlit golden highlight on top-right of straw hat!
  const hlHat = TH([[26, -162]])[0];
  st.glow(hlHat[0], hlHat[1], 30 * scale, 16 * scale, '#FFFDF5', 0.60, 'screen', 0.25);

  // Coral-red ribbon band around hat crown + cute trailing ribbon bow at the back!
  st.stroke(TH([[-44, -132], [-8, -124], [26, -124], [52, -128]]), {
    color: PAL.ribbon, width: 10 * scale, alpha: 0.88, blur: 0.3, rimStroke: 0.20,
  });
  // Sweet ribbon bow loops & fluttering tails at back of hat
  const bow1 = TH(ellipsePts(-50, -134, 14, 7, 10, -0.4));
  const bow2 = TH(ellipsePts(-54, -122, 13, 6.5, 10, 0.45));
  st.wash(bow1, { color: PAL.ribbon, color2: PAL.ribbonDeep, alpha: 0.88, layers: 4, blur: 0.3, rimStroke: 0.22 });
  st.wash(bow2, { color: PAL.ribbon, color2: PAL.ribbonDeep, alpha: 0.88, layers: 4, blur: 0.3, rimStroke: 0.22 });
  st.stroke(TH([[-48, -128], [-68, -104], [-78, -82]]), { color: PAL.ribbon, width: 7 * scale, alpha: 0.84, blur: 0.3 });
  st.stroke(TH([[-46, -126], [-58, -98], [-62, -76]]), { color: PAL.ribbonDeep, width: 6 * scale, alpha: 0.78, blur: 0.3 });

  // Delicate colored-pencil accents unifying the child
  const lp = { color: PAL.sepia, width: 1.3 * scale, alpha: 0.46, jitter: 0.35 * scale };
  const bp = { color: PAL.indigo, width: 1.3 * scale, alpha: 0.44, jitter: 0.35 * scale };
  st.pencil(TH(sampleCubic([50, -104], [56, -92], [60, -87], [55, -82], 8)), lp);
  st.pencil(TH(sampleCubic([55, -82], [52, -72], [44, -58], [24, -50], 8)), lp);
  st.pencil(TH(sampleCubic([-64, -122], [-18, -112], [42, -106], [82, -118], 10)), { color: '#9E7336', width: 1.25 * scale, alpha: 0.48 });
  st.pencil(T(sampleCubic([34, -28], [18, -20], [-4, -22], [-24, -32], 8)), { ...lp, alpha: 0.38 });
  st.pencil(T(sampleCubic([-42, -36], [-78, -4], [-94, 40], [-84, 70], 10)), bp);
  st.pencil(T(sampleCubic([-84, 70], [-64, 88], [-22, 86], [10, 72], 10)), bp);
  st.pencil(T(sampleCubic([14, 14], [22, 32], [28, 42], [34, 46], 6)), lp);
  st.pencil(T(sampleCubic([34, 46], [56, 62], [78, 74], [98, 82], 8)), lp);
  st.pencil(T(sampleCubic([136, 106], [100, 108], [46, 78], [8, 52], 10)), { ...lp, alpha: 0.38 });
  st.pencil(T(sampleCubic([36, 68], [42, 84], [22, 118], [2, 142], 10)), lp);
}

// ============================================================================
// 4. PAINTERLY BOTANICAL PROPS (Wet Mossy Stones, Willow Curtains, Reeds, Flowers)
// ============================================================================
export function drawRiverStone(st, cx, cy, rx, ry, opts = {}) {
  const { rot = 0, moss = true, inWater = true } = opts;
  const pts = ellipsePts(cx, cy, rx, ry, 18, rot);
  if (inWater) {
    // Soft underwater stone reflection
    st.wash(ellipsePts(cx, cy + ry * 0.72, rx * 0.94, ry * 0.55, 14, rot), {
      color: '#5B8AA6', alpha: 0.34, layers: 4, blur: 3.5, rimStroke: 0,
    });
  }
  st.reserve(pts, '#F7F4EA', 0.90, 0.5);
  st.wash(pts, { color: '#B5AEA0', color2: '#7A8CA3', alpha: 0.74, layers: 6, variance: 0.07, blur: 0.6, rimStroke: 0.28 });
  // Sunlit stone top highlight
  st.glow(cx + rx * 0.16, cy - ry * 0.22, rx * 0.55, ry * 0.35, '#FFFDF5', 0.42, 'screen', rot);
  if (moss) {
    st.wash(ellipsePts(cx - rx * 0.10, cy - ry * 0.28, rx * 0.62, ry * 0.38, 14, rot - 0.1), {
      color: '#A5D45C', color2: '#569E52', alpha: 0.72, layers: 6, variance: 0.16, blur: 0.8, rimStroke: 0.22,
    });
    st.glow(cx + rx * 0.08, cy - ry * 0.36, rx * 0.35, ry * 0.20, '#E8E874', 0.42, 'multiply');
  }
  st.pencil(pts.slice(0, 9), { color: '#5F6E7D', width: 1.1, alpha: 0.36, jitter: 0.4 });
  if (inWater) {
    st.ripple(cx, cy + ry * 0.75, rx * 1.18, ry * 0.34, { alpha: 0.58, thickness: 1.7 });
  }
}

export function drawFloatingLeaf(st, cx, cy, scale = 1.0, rot = -0.2) {
  const T = (pts) => xform(pts, cx, cy, scale, rot, false);
  const pts = T([[-44, 0], [-18, -11], [14, -9], [46, 0], [14, 10], [-18, 11]]);
  st.wash(T([[-40, 5], [42, 5], [18, 15], [-20, 15]]), { color: '#4584A6', alpha: 0.34, layers: 3, blur: 2.0, rimStroke: 0 });
  st.reserve(pts, '#FAF6D8', 0.92, 0.3);
  st.wash(pts, { color: '#CBE05C', color2: '#65AA50', alpha: 0.84, layers: 5, variance: 0.06, blur: 0.4, rimStroke: 0.28 });
  st.pencil(T([[-42, 0], [0, -1], [44, 0]]), { color: '#4A7A42', width: 1.1 * scale, alpha: 0.56 });
  st.ripple(cx, cy + 4 * scale, 54 * scale, 11 * scale, { alpha: 0.50, thickness: 1.4 * scale });
}

export function drawReedCluster(st, baseX, baseY, count = 8, height = 280, opts = {}) {
  const { lean = 0.2, colors = ['#98CA5E', '#58A258', '#3B7E52'], alpha = 0.68, blur = 0.4, width = 10 } = opts;
  for (let i = 0; i < count; i++) {
    const x0 = baseX + st.rng.range(-55, 55);
    const h = height * st.rng.range(0.62, 1.18);
    const bend = (lean + st.rng.range(-0.22, 0.22)) * h;
    st.stroke([
      [x0, baseY],
      [x0 + bend * 0.25, baseY - h * 0.35],
      [x0 + bend * 0.62, baseY - h * 0.70],
      [x0 + bend, baseY - h],
    ], {
      color: st.rng.pick(colors),
      width: width * st.rng.range(0.68, 1.25),
      alpha: alpha * st.rng.range(0.75, 1.08),
      taperStart: 0.65,
      taperEnd: 0.02,
      blur,
    });
  }
}

export function drawWillowBranch(st, startX, startY, length = 340, droop = 0.25, opts = {}) {
  const { colors = ['#A5D462', '#6EB358', '#4A9154'], alpha = 0.66, blur = 0.5, leafCount = 14 } = opts;
  const endX = startX + length * droop, endY = startY + length;
  const midX = (startX + endX) * 0.5 + st.rng.range(-18, 18), midY = (startY + endY) * 0.5;
  st.pencil([[startX, startY], [midX, midY], [endX, endY]], { color: '#587D49', width: 1.3, alpha: alpha * 0.72 });
  for (let i = 1; i <= leafCount; i++) {
    const t = i / (leafCount + 1);
    const lx = (1 - t) * (1 - t) * startX + 2 * (1 - t) * t * midX + t * t * endX;
    const ly = (1 - t) * (1 - t) * startY + 2 * (1 - t) * t * midY + t * t * endY;
    const side = i % 2 === 0 ? 1 : -1;
    const lLen = st.rng.range(28, 50);
    const ang = Math.PI * 0.5 + side * st.rng.range(0.30, 0.72);
    st.stroke([
      [lx, ly],
      [lx + Math.cos(ang) * lLen * 0.5, ly + Math.sin(ang) * lLen * 0.5],
      [lx + Math.cos(ang) * lLen, ly + Math.sin(ang) * lLen],
    ], {
      color: st.rng.pick(colors),
      width: st.rng.range(9, 14),
      alpha: alpha * st.rng.range(0.75, 1.08),
      taperStart: 0.15,
      taperEnd: 0.04,
      blur,
    });
  }
}

export function drawWildflower(st, cx, cy, scale = 1.0, petalColor = '#FFFFFF', centerColor = '#FFC640') {
  // Delicate stem & tiny leaf grounding the flower into the meadow!
  st.stroke([[cx, cy + 4 * scale], [cx - 2 * scale, cy + 16 * scale], [cx + 1 * scale, cy + 26 * scale]], {
    color: '#4F944C', width: 2.4 * scale, alpha: 0.72, rimStroke: 0,
  });
  st.stroke([[cx - 1 * scale, cy + 18 * scale], [cx + 9 * scale, cy + 12 * scale]], {
    color: '#6BB054', width: 4.0 * scale, alpha: 0.68, rimStroke: 0,
  });
  for (let i = 0; i < 5; i++) {
    const a = (i / 5) * Math.PI * 2 + st.rng.range(-0.15, 0.15);
    st.reserve(ellipsePts(cx + Math.cos(a) * 6.5 * scale, cy + Math.sin(a) * 6.5 * scale, 5.2 * scale, 3.6 * scale, 8, a), petalColor, 0.94);
  }
  st.reserve(ellipsePts(cx, cy, 3.5 * scale, 3.5 * scale, 8), centerColor, 0.96);
}
