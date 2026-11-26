import * as T from 'three';

const tau = Math.PI * 2;
const clamp = T.MathUtils.clamp;
const mix = T.MathUtils.lerp;
let seed = 39028;
export function random() {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  return seed / 4294967296;
}
const range = (a, b) => mix(a, b, random());
const pick = (items) => items[Math.floor(random() * items.length)];
const palette = (colors) => colors.map((color) => new T.Color(color));
const standard = (color, options = {}) => new T.MeshStandardMaterial({color, roughness: .87, ...options});
const facets = standard(0xffffff, {vertexColors: true, side: T.DoubleSide});
const box = new T.BoxGeometry(1, 1, 1);
const stone = new T.IcosahedronGeometry(1, 0);
const colors = {
  grass: palette([0x628052, 0x779257, 0x8fa260, 0x6f8a55, 0x819451, 0x96a365]),
  moss: palette([0x66754d, 0x708650, 0x889454]),
  earth: palette([0x826854, 0xa18469, 0x7f7665, 0x967768, 0xa38c74]),
  cliff: palette([0x545761, 0x62606a, 0x77717a, 0x686774, 0x8d7d79, 0x80766e]),
  granite: palette([0x777e81, 0x939797, 0x69757c, 0x8a8981, 0xa1a09a]),
  snow: palette([0xe1e7df, 0xf4f4e9, 0xd0dcd9, 0xbccccb]),
};

function mesh(parent, geometry, material, x, y, z, sx = 1, sy = 1, sz = 1) {
  const object = new T.Mesh(geometry, material);
  object.position.set(x, y, z);
  object.scale.set(sx, sy, sz);
  object.castShadow = true;
  object.receiveShadow = true;
  parent.add(object);
  return object;
}

function triangulate(rings, faceColor) {
  const vertices = [], pigments = [];
  function triangle(a, b, c, level, slice) {
    const color = faceColor(a, b, c, level, slice);
    for (const p of [a, b, c]) {
      vertices.push(p.x, p.y, p.z);
      pigments.push(color.r, color.g, color.b);
    }
  }
  for (let level = 1; level < rings.length; level++) {
    const inner = rings[level - 1], outer = rings[level];
    for (let i = 0; i < outer.length; i++) {
      const j = (i + 1) % outer.length;
      triangle(inner[i], inner[j], outer[j], level, i);
      triangle(inner[i], outer[j], outer[i], level, i);
    }
  }
  const geometry = new T.BufferGeometry();
  geometry.setAttribute('position', new T.Float32BufferAttribute(vertices, 3));
  geometry.setAttribute('color', new T.Float32BufferAttribute(pigments, 3));
  geometry.computeVertexNormals();
  return geometry;
}

function outline(angle) {
  return 1 + .058 * Math.sin(3 * angle + .4) + .055 * Math.sin(5 * angle - .6)
    + .026 * Math.cos(9 * angle + 1.2);
}
const radiusX = 5.12, radiusZ = 4.12;
function edgeRatio(x, z) {
  return Math.hypot(x / radiusX, z / radiusZ) / outline(Math.atan2(z / radiusZ, x / radiusX));
}
function bankX(z) {
  return .8 + .63 * Math.sin((z + .6) * .82);
}
function bankWidth(z) {
  return .33 + .65 * Math.exp(-((z + .92) ** 2) / .47) + .07 * Math.sin(z * 1.35);
}
function waterHeight(z) {
  return .55 - .068 * z;
}
function ground(x, z) {
  const distance = edgeRatio(x, z);
  const base = .43 + .62 * (1 - Math.min(1, distance) ** 2)
    + .11 * Math.sin(x * 1.25 + z * .62) + .09 * Math.cos(z * 1.9 - x * .3);
  const trench = (1 - T.MathUtils.smoothstep(Math.abs(x - bankX(z)), bankWidth(z) * .73, bankWidth(z) + .39))
    * T.MathUtils.smoothstep(z, -2.67, -1.85);
  return mix(base, waterHeight(z) - .17, trench);
}

function terrain(island) {
  const count = 80, rings = [];
  for (let level = 0; level <= 17; level++) {
    rings.push(Array.from({length: count}, (_, i) => {
      const a = i / count * tau + (level % 2 ? .014 : 0);
      const r = outline(a) * level / 17 * (level === 17 ? 1 : range(.984, 1.016));
      const x = Math.cos(a) * radiusX * r, z = Math.sin(a) * radiusZ * r;
      return {x, y: ground(x, z) + (level === 17 ? 0 : range(-.025, .025)), z};
    }));
  }
  mesh(island, triangulate(rings, (a, b, c) => {
    const x = (a.x + b.x + c.x) / 3, z = (a.z + b.z + c.z) / 3;
    const fade = .5 + .5 * Math.sin(x * 1.13 + Math.cos(z * 1.7)) * Math.cos(z * .65);
    return pick(colors.grass).clone().lerp(colors.moss[0], fade * .33);
  }), facets, 0, 0, 0);

  const strata = [[1.014, .24], [.972, -.12], [1.025, -.39], [.93, -1.04],
    [.8, -1.79], [.65, -2.42], [.46, -3], [.26, -3.45], [.018, -3.81]];
  const edges = rings.at(-1);
  const rockRings = [edges, ...strata.map(([size, y], level) => edges.map((point, i) => {
    const a = i / count * tau;
    const fracture = Math.sin(a * 13) * .045 + Math.cos(a * 19 + .5) * .037;
    const shelf = y + Math.sin(a * 3 + level * .37) * .15 + range(-.16, .16);
    return {
      x: point.x * size * (1 + fracture) - (level + 1) * .095,
      z: point.z * size * (1 + fracture) + (level + 1) * .035,
      y: shelf + (level < 2 ? (point.y - .4) * .7 : 0),
    };
  }))];
  mesh(island, triangulate(rockRings, (a, b, c, level, slice) => {
    if (level === 1) return pick(colors.moss);
    if (level <= 3) return pick(colors.earth);
    const tint = .5 + .5 * Math.cos(slice * .72 + level / 2);
    return pick(colors.cliff).clone().lerp(colors.earth[1], tint * (level === 5 ? .48 : .18))
      .multiplyScalar(1 - Math.max(0, level - 6) * .09);
  }), facets, 0, 0, 0);
}

function peak(island, x, z, width, depth, height, leaning, snowy) {
  const ringSize = 19;
  const ridges = Array.from({length: ringSize}, () => range(.8, 1.22));
  const contours = [[1, -.16], [.87, .14], [.67, .37], [.52, .54], [.35, .69], [.20, .85], [.075, .96], [0, 1]];
  const rings = contours.map(([r, y], level) => ridges.map((ridge, i) => {
    const angle = i / ringSize * tau + (level % 2 ? .056 : 0);
    const crag = level > 0 && level < 7 ? range(-.105, .103) : 0;
    return {
      x: x + r * width * ridge * Math.cos(angle) + y * leaning,
      z: z + r * depth * ridge * Math.sin(angle) - y * .2,
      y: ground(x, z) + height * (y + crag) - (level === 0 ? .28 : 0),
    };
  }));
  const geometry = triangulate(rings.reverse(), (a, b, c, level, slice) => {
    const snowLine = 2.75 + .31 * Math.sin(slice * 1.27) + .24 * Math.cos(slice * .6);
    const mean = (a.y + b.y + c.y) / 3;
    if (snowy && mean > snowLine) return pick(colors.snow);
    if (level >= 6) return pick(colors.moss).clone().lerp(pick(colors.granite), level === 7 ? .19 : .46);
    return pick(colors.granite);
  });
  mesh(island, geometry, facets, 0, 0, 0);
}

function instances(parent, geometry, items, casting = true) {
  const group = new T.InstancedMesh(geometry, standard(0xffffff), items.length);
  const transform = new T.Object3D();
  items.forEach(({p, s, y = 0, lean = 0, color}, index) => {
    transform.position.set(...p);
    transform.scale.set(...s);
    transform.rotation.set(lean, y, lean * .4);
    transform.updateMatrix();
    group.setMatrixAt(index, transform.matrix);
    group.setColorAt(index, color);
  });
  group.castShadow = casting;
  group.receiveShadow = true;
  parent.add(group);
}

const cabinX = 2.55, cabinZ = .56;
function pathX(z) {
  return cabinX + .34 * Math.sin((z - .7) * 1.8);
}
const onPath = (x, z) => z > .65 && z < 2.62 && Math.abs(pathX(z) - x) < .22;
const inWater = (x, z, margin = .1) => z > -2.32 && Math.abs(x - bankX(z)) < bankWidth(z) + margin;

function forest(island) {
  const needles = palette([0x234f43, 0x2a5948, 0x35664d, 0x437352, 0x527b56, 0x34604a, 0x698b5c]);
  const bark = new T.Color(0x655042), leaves = [], trunks = [];
  function pine(x, z, height) {
    const groundY = ground(x, z) - .04;
    const twist = range(0, tau);
    const width = height * range(.19, .265);
    const tint = pick(needles);
    trunks.push({p: [x, groundY + height * .28, z], s: [height * .054, height * .57, height * .054], color: bark});
    for (let i = 0; i < 4; i++) {
      const w = width * (1 - .194 * i);
      leaves.push({
        p: [x + range(-.035, .035), groundY + height * (.35 + i * .171), z + range(-.03, .03)],
        s: [w, height * (.42 - .023 * i), w],
        y: twist + i * .48, lean: range(-.08, .08), color: tint.clone().multiplyScalar(.88 + i * .075),
      });
    }
  }

  const planted = [];
  for (let i = 0; i < 950 && planted.length < 141; i++) {
    const x = range(-4.96, 4.96), z = range(-3.8, 3.8);
    if (edgeRatio(x, z) > .95 || inWater(x, z, .27) || onPath(x, z)) continue;
    if (Math.hypot(x - cabinX, z - cabinZ) < 1.13) continue;
    if (((x + 2.0) / 2.9) ** 2 + ((z + 1.29) / 1.70) ** 2 < 1) continue;
    if (planted.some(([px, pz]) => Math.hypot(px - x, pz - z) < .37)) continue;
    const size = range(.39, 1.06) * (x < .1 ? 1.14 : .9);
    planted.push([x, z]);
    pine(x, z, size);
  }
  for (const [x, z, h] of [[3.72,-.16,1.42], [3.24,-.66,1.25], [-3.27,1.38,1.38], [-2.74,2.01,1.46]]) pine(x, z, h);
  instances(island, new T.CylinderGeometry(.65, 1, 1, 5), trunks);
  instances(island, new T.CylinderGeometry(0, 1, 1, 7), leaves);

  const flowerColors = palette([0xf3db7a, 0xe8e5be, 0xd5a993, 0xdcb7a5]);
  const shrubs = [], flowers = [], gravel = [];
  for (let i = 0; i < 490; i++) {
    const x = range(-4.9, 4.9), z = range(-3.9, 3.9);
    if (edgeRatio(x, z) > .992 || inWater(x, z) || onPath(x, z) || Math.hypot(x - cabinX, z - cabinZ) < .78) continue;
    const size = range(.028, .12);
    const y = ground(x, z);
    shrubs.push({p: [x, y + .025, z], s: [size, size * .62, size * .8], color: pick(needles), y: range(0, tau)});
    if (random() < .3) {
      flowers.push({p: [x + .02, y + size * .63, z], s: [.034, .025, .034], color: pick(flowerColors)});
    }
  }
  for (let i = 0; i < 93; i++) {
    const z = range(-1.62, 3.38);
    const x = bankX(z) + pick([-1, 1]) * (bankWidth(z) + range(.08, .28));
    if (edgeRatio(x, z) > .99) continue;
    const r = range(.048, .17);
    gravel.push({p: [x, ground(x, z) + r * .15, z], s: [r, r * .61, r * .71], color: pick(colors.granite), y: range(0, tau)});
  }
  for (let i = 0; i < 25; i++) {
    const z = .88 + i * .068, x = pathX(z) + range(-.10, .10);
    gravel.push({p: [x, ground(x, z) + .028, z], s: [.16, .045, .076], color: pick(colors.earth), y: range(-.8, .8)});
  }
  instances(island, stone, shrubs, false);
  instances(island, stone, gravel);
  instances(island, stone, flowers, false);
}

function cottage(island) {
  const home = new T.Group();
  home.position.set(cabinX, ground(cabinX, cabinZ) - .07, cabinZ);
  home.rotation.y = .20;
  island.add(home);
  const timber = standard(0x644537), plank = standard(0xb47b53), trim = standard(0xe1b789);
  const roofing = [0x9c5141, 0xa45944, 0xb4644d, 0x914c42, 0x874238].map((c) => standard(c));
  const dark = standard(0x513a38), chimney = standard(0x8e7770), door = standard(0x72544a);
  const glass = standard(0xf6ae51, {emissive: 0xffa840, emissiveIntensity: .8});
  const block = (material, x, y, z, w, h, d, parent = home) => mesh(parent, box, material, x, y, z, w, h, d);
  block(chimney, 0, .085, 0, 1.22, .19, .96);
  block(plank, 0, .54, 0, 1.16, .85, .83);
  for (let level = 0; level < 9; level++) {
    const y = .16 + level * .098;
    for (const side of [-1, 1]) {
      block(level % 3 ? plank : trim, 0, y, side * .418, 1.19, .033, .024);
      block(level % 3 ? plank : trim, side * .579, y, 0, .028, .033, .84);
    }
  }
  for (const x of [-.565, .565]) for (const z of [-.41, .41]) block(timber, x, .54, z, .081, .9, .07);
  const gable = new T.Shape();
  gable.moveTo(-.58, 0);
  gable.lineTo(.58, 0);
  gable.lineTo(0, .53);
  gable.closePath();
  const gableGeometry = new T.ExtrudeGeometry(gable, {depth: .83, bevelEnabled: false});
  mesh(home, gableGeometry, plank, 0, .94, -.415);
  const pitch = .76;
  for (const side of [-1, 1]) {
    const slope = new T.Group();
    slope.position.set(side * .348, 1.204, 0);
    slope.rotation.z = -side * pitch;
    home.add(slope);
    block(dark, 0, 0, 0, .98, .059, 1.12, slope);
    for (let row = 0; row < 7; row++) {
      for (let column = 0; column < 9; column++) {
        const z = -.48 + column * .12 + (row % 2 ? .015 : 0);
        block(pick(roofing), -.414 + row * .138, .042 + range(0, .015), z, .15, .038, .12, slope);
      }
    }
    block(timber, 0, -.002, .552, 1.01, .078, .043, slope);
    block(timber, 0, -.002, -.552, 1.01, .078, .043, slope);
  }
  block(roofing[1], 0, 1.56, 0, .082, .076, 1.15);
  block(chimney, -.36, 1.465, -.24, .185, .50, .19);
  for (let i = 0; i < 4; i++) block(dark, -.36, 1.31 + i * .103, -.24, .194, .012, .20);
  block(chimney, -.36, 1.73, -.24, .232, .09, .231);
  block(dark, -.36, 1.779, -.24, .129, .013, .126);

  function window(x, y, z, rotation = 0, size = .27) {
    const frame = new T.Group();
    frame.position.set(x, y, z);
    frame.rotation.y = rotation;
    home.add(frame);
    block(timber, 0, 0, 0, size + .06, size + .06, .035, frame);
    block(glass, 0, 0, .021, size, size, .014, frame);
    block(trim, 0, 0, .034, .024, size, .017, frame);
    block(trim, 0, 0, .034, size, .024, .017, frame);
    block(trim, 0, -size * .5 - .018, .045, size + .09, .03, .07, frame);
  }
  window(.30, .64, .443);
  window(-.24, .67, -.438, Math.PI);
  window(.60, .64, .02, Math.PI / 2, .31);
  window(-.60, .64, -.05, -Math.PI / 2);
  window(0, 1.17, .427, 0, .135);
  block(timber, -.25, .40, .445, .34, .56, .035);
  block(door, -.25, .394, .473, .267, .49, .041);
  block(glass, -.178, .414, .501, .032, .032, .022);
  block(chimney, -.25, .108, .53, .49, .105, .25);
  block(chimney, -.25, .055, .661, .50, .08, .17);
  const lamp = new T.PointLight(0xffa94b, .12, 3.4, 1.8);
  lamp.position.set(.23, .63, .71);
  home.add(lamp);
  const sideLamp = new T.PointLight(0xff913a, .08, 2.7, 1.8);
  sideLamp.position.set(.77, .56, .04);
  home.add(sideLamp);
  const smokeSource = home.localToWorld(new T.Vector3(-.36, 1.80, -.24));
  return {glass, lamp, sideLamp, smokeSource};
}

function water(island) {
  const uniforms = {time: {value: 0}, night: {value: 0}, fall: {value: 0}};
  function sheet(rows, isFall) {
    const pos = [], uv = [], indices = [];
    rows.forEach(([x, y, z, half], i) => {
      for (let j = 0; j <= 12; j++) {
        pos.push(x + (j / 6 - 1) * half, y, z + (isFall ? .075 * Math.sin(j / 12 * Math.PI) : 0));
        uv.push(j / 12, i / (rows.length - 1));
        if (i && j) {
          const k = i * 13 + j;
          indices.push(k - 14, k - 1, k, k - 14, k, k - 13);
        }
      }
    });
    const geo = new T.BufferGeometry();
    geo.setAttribute('position', new T.Float32BufferAttribute(pos, 3));
    geo.setAttribute('uv', new T.Float32BufferAttribute(uv, 2));
    geo.setIndex(indices);
    const mat = new T.ShaderMaterial({
      transparent: isFall, depthWrite: !isFall, side: T.DoubleSide,
      uniforms: {...uniforms, fall: {value: Number(isFall)}},
      vertexShader: `
        varying vec2 st;
        void main() { st = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
      `,
      fragmentShader: `
        varying vec2 st;
        uniform float time, night, fall;
        void main() {
          float edge = abs(st.x * 2.0 - 1.0);
          float drift = st.y - time * mix(.09,.37,fall);
          float ripple = sin(drift * 138.0 + sin(st.x * 14.0 + st.y * 17.0) * 1.4);
          float glint = pow(max(0.0, ripple), 11.0) * (.5 + .5 * sin(st.x * 38.0 + drift * 16.0));
          float flow = st.x + .013 * sin(drift * 21.0 + st.x * 18.0);
          float threads = pow(.5 + .5 * sin(flow * 63.0 + sin(flow * 29.0) * 1.2), 3.0);
          float foam = max(glint * .21, smoothstep(.82, 1.0, edge) * (.30 + glint * .46));
          foam = mix(foam, .39 + .38 * threads + glint * .26 + .13 * smoothstep(.63, 1.0, st.y), fall);
          vec3 base = mix(vec3(.027,.41,.44), vec3(.035,.19,.32), night);
          vec3 spray = mix(vec3(.76,.94,.91), vec3(.36,.67,.79), night);
          float opacity = mix(1.0, (1.0 - smoothstep(.83,1.0,edge)) * (1.0 - smoothstep(.72,1.01,st.y)) * (.83 + threads * .17), fall);
          gl_FragColor = vec4(mix(base, spray, clamp(foam, 0.0, 1.0)), opacity);
          #include <colorspace_fragment>
        }
      `,
    });
    island.add(new T.Mesh(geo, mat));
  }
  const lip = 3.93;
  const river = Array.from({length: 70}, (_, i) => {
    const z = mix(-2.29, lip, i / 69);
    return [bankX(z), waterHeight(z), z, bankWidth(z) * T.MathUtils.smoothstep(z, -2.39, -1.86)];
  });
  sheet(river, false);
  const cataract = Array.from({length: 33}, (_, i) => {
    const t = i / 32;
    return [
      bankX(lip) - .07 * t, waterHeight(lip) - 4.28 * t ** 1.19,
      lip + .46 * Math.sin(t * Math.PI * .5) + .22 * t,
      bankWidth(lip) * (1 - .27 * t) + .24 * t ** 3,
    ];
  });
  sheet(cataract, true);
  return {uniforms, cataract};
}

export function makeIsland(island) {
  terrain(island);
  peak(island, -2.75, -.99, 1.47, 1.32, 2.55, -.48, true);
  peak(island, -.76, -2.14, 1.55, 1.30, 2.75, .13, true);
  peak(island, -1.86, -1.56, 1.97, 1.73, 3.83, -.39, true);
  peak(island, -2.60, -.41, 1.12, .89, 1.55, .36, false);
  peak(island, -.97, -.79, .94, .87, 1.80, -.25, false);
  forest(island);
  const cabin = cottage(island);
  return {...cabin, ...water(island)};
}
