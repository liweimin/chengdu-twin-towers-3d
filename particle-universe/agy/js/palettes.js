/**
 * Curated astrophotography-inspired cosmic palettes for AETHERIA.
 * All colors are stored as [r, g, b] tuples for fast canvas & p5 blending.
 */

const COSMIC_PALETTES = [
  {
    id: 'carina',
    name: '船底座极光',
    subtitle: 'CARINA AURORA',
    bgTop: [3, 5, 14],
    bgBottom: [8, 10, 26],
    nebula: [
      [32, 118, 198],   // deep celestial cyan-blue
      [126, 56, 178],   // cosmic amethyst
      [212, 112, 92],   // warm Carina dust
      [34, 166, 178]    // bioluminescent teal
    ],
    particles: [
      [115, 232, 255],  // electric cyan starlight
      [172, 142, 255],  // iris violet
      [255, 206, 138],  // warm celestial gold
      [255, 142, 186],  // nebula rose
      [232, 246, 255]   // starlight ivory
    ],
    burstCore: [255, 244, 214],
    burstRingA: [110, 236, 255],
    burstRingB: [255, 174, 128],
    singularity: [195, 150, 255]
  },
  {
    id: 'solaris',
    name: '日冕鎏金',
    subtitle: 'SOLARIS AMBER',
    bgTop: [6, 4, 12],
    bgBottom: [18, 9, 20],
    nebula: [
      [210, 116, 42],   // solar amber
      [148, 48, 86],    // deep crimson-plum
      [78, 52, 146],    // twilight indigo
      [245, 174, 88]    // corona gold
    ],
    particles: [
      [255, 224, 146],  // molten gold
      [255, 148, 94],   // solar coral
      [168, 132, 255],  // dusk violet
      [255, 192, 182],  // champagne blush
      [255, 248, 232]   // white-hot starlight
    ],
    burstCore: [255, 248, 220],
    burstRingA: [255, 205, 112],
    burstRingB: [255, 112, 126],
    singularity: [255, 184, 108]
  },
  {
    id: 'biolume',
    name: '深渊幽蓝',
    subtitle: 'BIOLUME ABYSS',
    bgTop: [2, 6, 14],
    bgBottom: [4, 18, 30],
    nebula: [
      [18, 148, 172],   // abyssal cyan
      [48, 72, 192],    // pelagic sapphire
      [98, 78, 204],    // aurora indigo
      [62, 212, 192]    // seafoam luminescence
    ],
    particles: [
      [102, 255, 232],  // aquamarine glow
      [112, 176, 255],  // glacial sapphire
      [180, 148, 255],  // moonlit lavender
      [196, 255, 248],  // ice starlight
      [238, 248, 255]   // pure silver-white
    ],
    burstCore: [232, 255, 252],
    burstRingA: [96, 255, 230],
    burstRingB: [130, 152, 255],
    singularity: [110, 238, 255]
  },
  {
    id: 'rosette',
    name: '玫瑰星云',
    subtitle: 'ROSETTE NEBULA',
    bgTop: [8, 4, 14],
    bgBottom: [20, 8, 26],
    nebula: [
      [196, 62, 128],   // rose-magenta gas
      [108, 64, 184],   // velvet violet
      [226, 138, 116],  // peach stardust
      [68, 116, 204]    // sapphire fringe
    ],
    particles: [
      [255, 138, 192],  // blossom magenta
      [255, 214, 168],  // champagne gold
      [138, 176, 255],  // cornflower star
      [238, 158, 255],  // orchid light
      [255, 244, 250]   // pearl white
    ],
    burstCore: [255, 240, 246],
    burstRingA: [255, 142, 198],
    burstRingB: [255, 216, 152],
    singularity: [255, 156, 216]
  }
];

const FLOW_MODES = [
  { id: 'drift', name: '星河漫流', subtitle: 'COSMIC DRIFT' },
  { id: 'spiral', name: '旋涡星系', subtitle: 'SPIRAL NEBULA' },
  { id: 'harmonic', name: '谐波星轨', subtitle: 'HARMONIC ORBIT' }
];

function lerpRgb(a, b, t) {
  return [
    a[0] + (b[0] - a[0]) * t,
    a[1] + (b[1] - a[1]) * t,
    a[2] + (b[2] - a[2]) * t
  ];
}

function clonePalette(p) {
  return {
    bgTop: [...p.bgTop],
    bgBottom: [...p.bgBottom],
    nebula: p.nebula.map(c => [...c]),
    particles: p.particles.map(c => [...c]),
    burstCore: [...p.burstCore],
    burstRingA: [...p.burstRingA],
    burstRingB: [...p.burstRingB],
    singularity: [...p.singularity]
  };
}

function blendPaletteInto(current, target, rate) {
  for (let i = 0; i < 3; i++) {
    current.bgTop[i] += (target.bgTop[i] - current.bgTop[i]) * rate;
    current.bgBottom[i] += (target.bgBottom[i] - current.bgBottom[i]) * rate;
    current.burstCore[i] += (target.burstCore[i] - current.burstCore[i]) * rate;
    current.burstRingA[i] += (target.burstRingA[i] - current.burstRingA[i]) * rate;
    current.burstRingB[i] += (target.burstRingB[i] - current.burstRingB[i]) * rate;
    current.singularity[i] += (target.singularity[i] - current.singularity[i]) * rate;
  }
  for (let k = 0; k < current.nebula.length; k++) {
    for (let i = 0; i < 3; i++) {
      current.nebula[k][i] += (target.nebula[k][i] - current.nebula[k][i]) * rate;
    }
  }
  for (let k = 0; k < current.particles.length; k++) {
    for (let i = 0; i < 3; i++) {
      current.particles[k][i] += (target.particles[k][i] - current.particles[k][i]) * rate;
    }
  }
}
