import * as T from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {makeIsland, random} from './island.js';

const viewport = document.querySelector('#viewport');
const experience = document.querySelector('.experience');
const status = document.querySelector('#status');
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const mobile = matchMedia('(max-width: 740px)');
const mix = T.MathUtils.lerp;
const smooth = T.MathUtils.smoothstep;
const range = (a, b) => mix(a, b, random());
const scene = new T.Scene();
const camera = new T.OrthographicCamera(-8, 8, 6, -6, .1, 110);
camera.position.set(10.6, 8.6, 15.2);

const renderer = new T.WebGLRenderer({alpha: true, antialias: true, powerPreference: 'high-performance'});
renderer.setClearColor(0x000000, 0);
renderer.toneMapping = T.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.28;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = T.PCFShadowMap;
renderer.shadowMap.autoUpdate = false;
viewport.append(renderer.domElement);

const controls = new OrbitControls(camera, viewport);
let needsRender = true;
const queueRender = () => { needsRender = true; };
controls.addEventListener('change', queueRender);
reducedMotion.addEventListener('change', queueRender);
controls.target.set(0, .23, 0);
controls.enableDamping = true;
controls.dampingFactor = .095;
controls.enablePan = false;
controls.minZoom = .67;
controls.maxZoom = 2.5;
controls.minPolarAngle = .24;
controls.maxPolarAngle = 1.66;
controls.rotateSpeed = .57;
controls.zoomSpeed = .78;
controls.update();
controls.saveState();

const daylight = new T.DirectionalLight(0xffead0, 2.6);
daylight.position.set(-5, 10, 6);
daylight.castShadow = true;
daylight.shadow.mapSize.set(2048, 2048);
Object.assign(daylight.shadow.camera, {left: -7, right: 7, top: 7, bottom: -7, near: .5, far: 29});
daylight.shadow.camera.updateProjectionMatrix();
daylight.shadow.bias = -.00023;
daylight.shadow.normalBias = .024;
const hemi = new T.HemisphereLight(0xd9eee9, 0x827066, 1.75);
const rim = new T.DirectionalLight(0xe2ecff, .65);
rim.position.set(4, 4, -7);
scene.add(daylight, hemi, rim);

const island = new T.Group();
scene.add(island);
const features = makeIsland(island);

function texture(width, height, draw) {
  const surface = document.createElement('canvas');
  surface.width = width;
  surface.height = height;
  draw(surface.getContext('2d'), width, height);
  const map = new T.CanvasTexture(surface);
  map.colorSpace = T.SRGBColorSpace;
  return map;
}

function cloudTexture() {
  const puffs = Array.from({length: 19}, (_, i) => {
    const x = .13 + .74 * i / 18 + range(-.044, .044);
    const top = 1 - Math.abs(x - .5) * 1.2;
    return [x, range(.45, .61) - top * range(0, .22), range(.074, .15), range(.13, .23) * top];
  });
  return texture(384, 176, (ctx, width, height) => {
    const image = ctx.createImageData(width, height);
    function density(x, y) {
      let shape = 0;
      for (const [cx, cy, rx, ry] of puffs) {
        const dist = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2;
        shape = Math.max(shape, 1 - dist);
      }
      const fine = Math.sin(105 * x + 61 * y) * Math.sin(112 * y - 39 * x) * .018
        + Math.sin(56 * x - 33 * y) * Math.sin(69 * y + 27 * x) * .028;
      return shape + fine;
    }
    for (let row = 0; row < height; row++) {
      for (let column = 0; column < width; column++) {
        const x = column / width, y = row / height;
        const d = density(x, y);
        const alpha = smooth(d, .035, .56) * (1 - smooth(y, .62, .87));
        if (alpha === 0) continue;
        const edge = T.MathUtils.clamp((d - density(x + .014, y + .027)) * 2.6, -.55, .33);
        const light = T.MathUtils.clamp(.64 + (.56 - y) * 1.32 + edge + d * .15, 0, 1);
        const j = (row * width + column) * 4;
        image.data[j] = mix(162, 255, light);
        image.data[j + 1] = mix(182, 254, light);
        image.data[j + 2] = mix(189, 241, light);
        image.data[j + 3] = alpha * 255;
      }
    }
    ctx.putImageData(image, 0, 0);
  });
}

const glow = texture(64, 64, (ctx) => {
  const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  gradient.addColorStop(0, 'rgba(255,255,255,1)');
  gradient.addColorStop(.22, 'rgba(255,255,255,.67)');
  gradient.addColorStop(.56, 'rgba(255,255,255,.21)');
  gradient.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 64, 64);
});
const cloudMaps = [cloudTexture(), cloudTexture(), cloudTexture()];
const clouds = [];
function puff(map, x, y, z, width, height, opacity) {
  const material = new T.SpriteMaterial({map, transparent: true, depthWrite: false, toneMapped: false, opacity});
  const sprite = new T.Sprite(material);
  sprite.position.set(x, y, z);
  sprite.scale.set(width, height, 1);
  scene.add(sprite);
  return sprite;
}
function cloud(x, y, z, width, height, opacity) {
  const sprite = puff(cloudMaps[clouds.length % cloudMaps.length], x, y, z, width, height, opacity);
  clouds.push({sprite, x, y, z, opacity, phase: range(0, 6.28)});
}
// Cloud banks sit at different heights so orbiting reveals depth through the haze.
for (let i = 0; i < 37; i++) {
  const angle = i * 2.39996, r = range(7.2, 20.5);
  cloud(Math.cos(angle) * r, range(-7.7, -4.15), Math.sin(angle) * r, range(5.8, 13), range(2.0, 4.05), range(.25, .71));
}
cloud(-6.2, -1.45, -.8, 6.0, 2.42, .69);
cloud(5.95, -.85, -3.4, 6.7, 2.42, .84);
cloud(6.1, -2.45, 2.1, 5.5, 2.16, .67);
cloud(-4.7, -3.05, 3.4, 6.2, 2.4, .78);
cloud(-.8, -3.98, 5.17, 6.06, 2.24, .69);
cloud(.7, -3.65, 4.58, 4.6, 1.75, .81);

const mist = Array.from({length: 11}, (_, i) => {
  const sprite = puff(glow, 0, 0, 0, 1.6, .56, .4);
  return {sprite, phase: i / 11, x: range(-.62, .62), z: range(-.41, .41)};
});
const smoke = Array.from({length: 9}, (_, i) => ({
  sprite: puff(glow, 0, 0, 0, .24, .24, .39), phase: i / 9,
}));

const sprayGeometry = new T.BufferGeometry();
const sprayData = Array.from({length: 130}, () => ({
  phase: random(), u: range(-1, 1), vx: range(-.54, .54), vz: range(-.19, .52),
}));
const sprayPosition = new T.Float32BufferAttribute(new Float32Array(sprayData.length * 3), 3);
sprayGeometry.setAttribute('position', sprayPosition);
const sprayMaterial = new T.PointsMaterial({
  color: 0xe8fff6, map: glow, size: .029, transparent: true, depthWrite: false, opacity: .84, toneMapped: false,
});
const droplets = new T.Points(sprayGeometry, sprayMaterial);
droplets.frustumCulled = false;
scene.add(droplets);

const sky = document.createElement('canvas');
sky.className = 'night-sky';
sky.setAttribute('aria-hidden', 'true');
experience.insertBefore(sky, viewport);
const skyContext = sky.getContext('2d');
const stars = Array.from({length: 182}, () => [random(), random() * .86, range(.42, 1.43), range(.21, .89)]);
function paintSky(width, height) {
  const dpr = Math.min(devicePixelRatio, 1.5);
  sky.width = Math.round(width * dpr);
  sky.height = Math.round(height * dpr);
  skyContext.scale(dpr, dpr);
  for (const [x, y, size, opacity] of stars) {
    skyContext.fillStyle = `rgba(236,243,255,${opacity * (1 - .58 * y)})`;
    skyContext.beginPath();
    skyContext.arc(x * width, y * height, size, 0, Math.PI * 2);
    skyContext.fill();
  }
  const x = width * .79, y = height * (mobile.matches ? .23 : .185);
  const radius = T.MathUtils.clamp(width * .026, 16, 39);
  const halo = skyContext.createRadialGradient(x, y, radius * .3, x, y, radius * 4);
  halo.addColorStop(0, '#f9e7af65');
  halo.addColorStop(.26, '#c8def33f');
  halo.addColorStop(1, '#c8def300');
  skyContext.fillStyle = halo;
  skyContext.fillRect(x - radius * 4, y - radius * 4, radius * 8, radius * 8);
  skyContext.save();
  skyContext.beginPath();
  skyContext.arc(x, y, radius, 0, Math.PI * 2);
  skyContext.clip();
  const moon = skyContext.createLinearGradient(x - radius, y - radius, x + radius, y + radius);
  moon.addColorStop(0, '#fff4cb');
  moon.addColorStop(1, '#d4dcdd');
  skyContext.fillStyle = moon;
  skyContext.fillRect(x - radius, y - radius, radius * 2, radius * 2);
  for (const [cx, cy, size] of [[-.46,-.22,.32],[.2,.39,.27],[.47,-.34,.19],[-.24,.58,.16],[.5,.18,.11],[-.06,-.56,.14]]) {
    const cr = radius * size, px = x + cx * radius, py = y + cy * radius;
    const crater = skyContext.createRadialGradient(px, py, 0, px, py, cr);
    crater.addColorStop(0, '#98adba57');
    crater.addColorStop(1, '#98adba00');
    skyContext.fillStyle = crater;
    skyContext.fillRect(px - cr, py - cr, cr * 2, cr * 2);
  }
  skyContext.restore();
}

function resize() {
  const {clientWidth: width, clientHeight: height} = viewport;
  if (!width || !height) return;
  const aspect = width / height;
  const viewHeight = mobile.matches ? Math.max(12.4, 12.25 / aspect) : Math.max(13.1, 14.4 / aspect);
  camera.top = viewHeight / 2;
  camera.bottom = -camera.top;
  camera.right = camera.top * aspect;
  camera.left = -camera.right;
  const shiftX = mobile.matches ? (aspect > 1.25 ? .19 : .025) : .153;
  const shiftY = mobile.matches && aspect < 1.25 ? .06 : -.009;
  camera.setViewOffset(width, height, -width * shiftX, -height * shiftY, width, height);
  renderer.setPixelRatio(Math.min(devicePixelRatio, mobile.matches ? 1.5 : 1.8));
  renderer.setSize(width, height, false);
  paintSky(width, height);
  queueRender();
}
new ResizeObserver(resize).observe(viewport);
resize();

let dayTarget = 0, night = 0;
const themes = [...document.querySelectorAll('[data-theme]')];
for (const button of themes) button.addEventListener('click', () => {
  const mode = button.dataset.theme;
  dayTarget = Number(mode === 'night');
  experience.dataset.mode = mode;
  document.querySelector('#scene-label').textContent = dayTarget ? '夜晚' : '白昼';
  document.querySelector('meta[name="theme-color"]').content = dayTarget ? '#122339' : '#e8ece2';
  for (const theme of themes) theme.setAttribute('aria-pressed', String(theme === button));
  queueRender();
});
const reset = document.querySelector('#reset');
reset.addEventListener('click', () => controls.reset());

const fullscreen = document.querySelector('#fullscreen');
fullscreen.hidden = !document.fullscreenEnabled;
fullscreen.addEventListener('click', async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await experience.requestFullscreen();
  } catch {
    fullscreen.hidden = true;
  }
});
document.addEventListener('fullscreenchange', () => {
  const label = document.fullscreenElement ? '退出全屏' : '全屏';
  fullscreen.title = label;
  fullscreen.setAttribute('aria-label', label);
});

viewport.addEventListener('keydown', (event) => {
  const {key} = event;
  if (key === 'Home') {
    event.preventDefault();
    controls.reset();
    return;
  }
  if (key === '+' || key === '=' || key === '-') {
    event.preventDefault();
    camera.zoom = T.MathUtils.clamp(camera.zoom * (key === '-' ? .9 : 1.1), controls.minZoom, controls.maxZoom);
    camera.updateProjectionMatrix();
    queueRender();
    return;
  }
  if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(key)) return;
  event.preventDefault();
  const spherical = new T.Spherical().setFromVector3(camera.position.clone().sub(controls.target));
  spherical.theta += key === 'ArrowLeft' ? .11 : key === 'ArrowRight' ? -.11 : 0;
  spherical.phi = T.MathUtils.clamp(spherical.phi + (key === 'ArrowUp' ? -.09 : key === 'ArrowDown' ? .09 : 0), controls.minPolarAngle, controls.maxPolarAngle);
  camera.position.setFromSpherical(spherical).add(controls.target);
  controls.update();
});

const warm = new T.Color(0xffe7c9), moonlight = new T.Color(0x9abaff);
const daySky = new T.Color(0xd8eee4), nightSky = new T.Color(0x94afe0);
const dayEarth = new T.Color(0x827061), nightEarth = new T.Color(0x4c5e89);
const cloudDay = new T.Color(0xffffff), cloudNight = new T.Color(0x5b7397);
const sprayDay = new T.Color(0xe9fff9), sprayNight = new T.Color(0x9bc9e6);
const end = features.cataract.at(-1);

function animateAtmosphere(time) {
  daylight.color.copy(warm).lerp(moonlight, night);
  daylight.intensity = mix(2.65, .89, night);
  hemi.color.copy(daySky).lerp(nightSky, night);
  hemi.groundColor.copy(dayEarth).lerp(nightEarth, night);
  hemi.intensity = mix(1.67, .79, night);
  rim.intensity = mix(.64, .74, night);
  renderer.toneMappingExposure = mix(1.18, .92, night);
  features.glass.emissiveIntensity = mix(.65, 2.6, night) + night * Math.sin(time * 2.4) * .07;
  features.lamp.intensity = mix(.11, 2.48, night);
  features.sideLamp.intensity = mix(.07, 1.45, night);
  features.uniforms.time.value = time;
  features.uniforms.night.value = night;
  for (const {sprite, x, y, z, phase, opacity} of clouds) {
    sprite.position.set(x + Math.sin(time * .097 + phase) * .48, y + Math.sin(time * .15 + phase) * .16, z);
    sprite.material.color.copy(cloudDay).lerp(cloudNight, night);
    sprite.material.opacity = opacity * mix(1, .83, night);
  }
  for (const {sprite, phase, x, z} of mist) {
    const t = (time * .24 + phase) % 1;
    sprite.position.set(end[0] + x * (1 + t * 2.8), end[1] + .31 + t * .34, end[2] + z + .38 * t);
    sprite.scale.set(.89 + t * 2.5, .32 + t * .65, 1);
    sprite.material.color.copy(sprayDay).lerp(sprayNight, night);
    sprite.material.opacity = Math.sin(t * Math.PI) * mix(.38, .25, night);
  }
  for (const {sprite, phase} of smoke) {
    const t = (time * .31 + phase) % 1;
    sprite.position.copy(features.smokeSource);
    sprite.position.x -= t ** 1.35 * .66;
    sprite.position.y += t * 1.43;
    sprite.position.z += Math.sin(t * 5 + time * .37) * t * .18;
    sprite.scale.setScalar(.15 + t * .70);
    sprite.material.color.copy(cloudDay).lerp(cloudNight, night);
    sprite.material.opacity = (1 - t) * mix(.63, .51, night);
  }
  sprayMaterial.color.copy(sprayDay).lerp(sprayNight, night);
  sprayData.forEach(({phase, u, vx, vz}, index) => {
    const t = (phase + time * .29) % 1;
    const row = Math.min(31, Math.floor(t * 32));
    const progress = t * 32 - row;
    const a = features.cataract[row], b = features.cataract[row + 1];
    sprayPosition.setXYZ(index,
      mix(a[0], b[0], progress) + u * mix(a[3], b[3], progress) + vx * t ** 2,
      mix(a[1], b[1], progress),
      mix(a[2], b[2], progress) + .10 + vz * t);
  });
  sprayPosition.needsUpdate = true;
}

renderer.shadowMap.needsUpdate = true;
animateAtmosphere(0);
renderer.render(scene, camera);
status.hidden = true;
reset.disabled = false;

let elapsed = 0, lastFrame;
renderer.setAnimationLoop((now) => {
  const delta = lastFrame === undefined ? 0 : Math.min(.05, (now - lastFrame) * .001);
  lastFrame = now;
  const still = reducedMotion.matches;
  if (!still) elapsed += delta;
  night = still ? dayTarget : mix(night, dayTarget, 1 - Math.exp(-delta * 4.4));
  controls.update();
  if (still && !needsRender) return;
  needsRender = false;
  animateAtmosphere(elapsed);
  renderer.render(scene, camera);
});
