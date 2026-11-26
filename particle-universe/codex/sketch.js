(() => {
  'use strict';

  const sky = document.querySelector('#sky');
  const pauseButton = document.querySelector('#pause');
  const fullscreenButton = document.querySelector('#fullscreen');
  const swatches = document.querySelectorAll('[data-palette]');

  if (typeof window.p5 !== 'function') {
    document.querySelector('#sketch-error').hidden = false;
    [pauseButton, fullscreenButton, ...swatches].forEach(button => { button.disabled = true; });
    return;
  }

  const palettes = {
    amber: {
      accent: '#e6bd8e', space: [22, 32, 79], cloud: [54, 91, 172],
      colors: [[99, 154, 246], [151, 194, 255], [205, 213, 255], [223, 143, 106], [255, 194, 129], [255, 231, 188]],
    },
    jade: {
      accent: '#8ddcbd', space: [16, 47, 68], cloud: [34, 150, 136],
      colors: [[65, 168, 202], [99, 224, 214], [182, 247, 223], [109, 161, 135], [157, 225, 160], [242, 249, 191]],
    },
    rose: {
      accent: '#e7a0c6', space: [50, 27, 78], cloud: [103, 71, 166],
      colors: [[138, 118, 247], [165, 147, 255], [209, 186, 250], [211, 113, 160], [252, 148, 190], [255, 208, 210]],
    },
  };

  const TAU = Math.PI * 2;
  const TILT = -0.26;
  const COS_TILT = Math.cos(TILT);
  const SIN_TILT = Math.sin(TILT);
  const INCLINATION = 0.64;
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const mix = (start, end, amount) => start + (end - start) * amount;
  const rgba = (color, alpha) => `rgba(${color.join(',')},${clamp(alpha, 0, 1)})`;
  const armAngle = radius => 1.53 + 2.65 * Math.log(radius + 0.21);

  new p5(p => {
    let backdrop;
    let trails;
    let layout;
    let dust = [];
    let beacons = [];
    let pulses = [];
    let palette = palettes.amber;
    let paused = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let time = 0;
    const pointer = { x: 0, y: 0, inside: false, energy: 0, opacity: 0 };
    const trailBins = Array.from({ length: 18 }, () => []);

    function getLayout(width, height) {
      const portrait = width <= 740 && height > width;
      return {
        x: width * (portrait ? 0.51 : 0.624),
        y: height * (portrait ? 0.59 : 0.51),
        radius: portrait ? Math.min(width * 0.69, height * 0.39) : Math.min(width * 0.425, height * 0.71),
        interaction: clamp(Math.min(width, height) * 0.205, 82, 185),
      };
    }

    function project(radius, angle, depth = 0) {
      const flatX = Math.cos(angle) * radius;
      const flatY = Math.sin(angle) * radius * INCLINATION + depth;
      return {
        x: layout.x + (flatX * COS_TILT - flatY * SIN_TILT) * layout.radius,
        y: layout.y + (flatX * SIN_TILT + flatY * COS_TILT) * layout.radius,
      };
    }

    function glow(ctx, x, y, radius, color, alpha, flatten = 1, angle = 0) {
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(angle);
      ctx.scale(1, flatten);
      const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, radius);
      gradient.addColorStop(0, rgba(color, alpha));
      gradient.addColorStop(0.18, rgba(color, alpha * 0.49));
      gradient.addColorStop(0.49, rgba(color, alpha * 0.13));
      gradient.addColorStop(1, rgba(color, 0));
      ctx.fillStyle = gradient;
      ctx.fillRect(-radius, -radius, radius * 2, radius * 2);
      ctx.restore();
    }

    function paintGas(ctx) {
      const width = Math.min(510, Math.ceil(p.width * 0.52));
      const height = Math.ceil(width * p.height / p.width);
      const gas = p.createImage(width, height);
      gas.loadPixels();
      const warm = palette.colors[4];
      const cool = palette.cloud;

      for (let row = 0; row < height; row++) {
        const y = ((row + 0.5) * p.height / height - layout.y) / layout.radius;
        for (let col = 0; col < width; col++) {
          const x = ((col + 0.5) * p.width / width - layout.x) / layout.radius;
          const u = x * COS_TILT + y * SIN_TILT;
          const v = (y * COS_TILT - x * SIN_TILT) / INCLINATION;
          const radius = Math.hypot(u, v);
          if (radius > 1.27) continue;

          // The glow and the moving dust use the same spiral geometry.
          const turbulence = p.noise(12 + u * 3.8, 12 + v * 3.8);
          const grain = p.noise(31 + u * 22, 31 + v * 22);
          const bend = Math.sin(Math.atan2(v, u) - armAngle(radius) + (turbulence - 0.5) * 1.32);
          const arm = Math.exp(-Math.pow(bend * (2.7 + radius * 2.8), 2));
          const extent = Math.pow(Math.max(0, 1 - radius / 1.27), 0.83);
          const billow = Math.pow(clamp(turbulence * 0.95 + grain * 0.65, 0, 1), 3.1);
          const core = Math.exp(-radius * 15);
          const heat = clamp(Math.exp(-radius * 4.7) * 1.12 + arm * Math.max(0, turbulence - 0.53) * 1.3, 0, 1);
          const opacity = extent * billow * (0.22 + arm * 1.37) + core * 0.67;
          const index = 4 * (row * width + col);
          for (let channel = 0; channel < 3; channel++) gas.pixels[index + channel] = mix(cool[channel], warm[channel], heat);
          gas.pixels[index + 3] = Math.min(1, opacity) * 255;
        }
      }

      gas.updatePixels();
      ctx.drawImage(gas.canvas, 0, 0, p.width, p.height);
    }

    function paintFilaments(ctx) {
      for (let strand = 0; strand < 150; strand++) {
        const arm = strand % 2 * Math.PI;
        const offset = p.randomGaussian(0, 0.3);
        const pitch = p.random(0.91, 1.09);
        const start = p.random(0.055, 0.84);
        const length = p.random(0.11, 0.52);
        const color = palette.colors[(start < 0.29 || p.random() < 0.25) ? 3 : strand % 2];
        const width = p.random(0.3, 0.85);
        ctx.lineWidth = width;

        // Fade both ends of each wisp so contours break up into separate clouds.
        for (let fragment = 0; fragment < 5; fragment++) {
          const strength = Math.sin((fragment + 0.5) * Math.PI / 5);
          ctx.strokeStyle = rgba(color, strength * (strand % 9 === 0 ? 0.10 : 0.037));
          ctx.beginPath();
          for (let i = 0; i <= 8; i++) {
            const progress = (fragment + i / 8) / 5;
            const radius = start + length * progress;
            const wave = p.noise(strand * 0.17, progress * 2.2) - 0.5;
            const point = project(radius, armAngle(radius) * pitch + arm + offset + wave * 0.16);
            if (i === 0) ctx.moveTo(point.x, point.y);
            else ctx.lineTo(point.x, point.y);
          }
          ctx.stroke();
        }
      }
    }

    function makeBackdrop() {
      p.randomSeed(62831);
      p.noiseSeed(47);
      const ctx = backdrop.drawingContext;
      backdrop.background(4, 7, 15);
      ctx.globalCompositeOperation = 'lighter';
      glow(ctx, layout.x, layout.y, layout.radius * 1.59, palette.space, 0.69, 0.71, TILT);
      glow(ctx, p.width * 0.92, p.height * 0.24, p.width * 0.49, palette.space, 0.2, 0.56, TILT);
      paintGas(ctx);
      paintFilaments(ctx);

      const stars = clamp(Math.round(p.width * p.height / 730), 470, 3000);
      beacons = [];
      for (let i = 0; i < stars; i++) {
        const x = p.random(p.width);
        const y = p.random(p.height);
        const size = p.random(0.36, 0.98) * (i % 17 === 0 ? 1.7 : 1);
        const color = palette.colors[i % 9 < 7 ? i % 3 : 4];
        const depth = x < p.width * 0.31 ? 0.64 : 1;
        ctx.fillStyle = rgba(color, p.random(0.11, 0.67) * depth);
        ctx.fillRect(x, y, size, size);
        if (i % 45 === 0) beacons.push({ x, y, color, size: size * p.random(1.35, 3.6), phase: p.random(TAU) });
      }

      for (let i = 0; i < 14000; i++) {
        const radius = p.random(0.025, 1.2);
        const angle = armAngle(radius) + (i % 2) * Math.PI + p.randomGaussian(0, 0.27 + 0.12 * radius);
        const point = project(radius, angle, p.randomGaussian(0, 0.024));
        const index = p.random() < Math.exp(-radius * 2.1) ? 3 + i % 3 : i % 3;
        ctx.fillStyle = rgba(palette.colors[index], p.random(0.08, 0.37) * (1 - radius * 0.46));
        const size = p.random(0.44, 1.2);
        ctx.fillRect(point.x, point.y, size, size);
      }

      const core = palette.colors[5];
      glow(ctx, layout.x, layout.y, layout.radius * 0.44, palette.colors[3], 0.20, 0.62, TILT);
      glow(ctx, layout.x, layout.y, layout.radius * 0.18, core, 0.36, 0.58, TILT);
      glow(ctx, layout.x, layout.y, layout.radius * 0.052, core, 0.51, 0.58, TILT);
      ctx.globalCompositeOperation = 'source-over';
    }

    function makeDust() {
      p.randomSeed(42019);
      const count = clamp(Math.round(p.width * p.height / 185), 2700, 9000);
      dust = Array.from({ length: count }, (_, index) => {
        const radius = 0.018 + 1.17 * p.random() ** (index % 8 === 0 ? 1.85 : 0.85);
        const orbital = index % 12 === 0;
        const spread = p.randomGaussian(0, 0.22 + radius * 0.18);
        const heat = p.random() < Math.exp(-radius * 2.6) + (orbital ? 0.18 : 0);
        return {
          radius, orbital,
          angle: orbital ? p.random(TAU) : (index % 2) * Math.PI + spread,
          speed: p.random(0.27, 0.85),
          depth: p.randomGaussian(0, 0.026 + radius * 0.015),
          phase: p.random(TAU),
          color: (heat ? 3 : 0) + index % 3,
          light: index % 29 === 0 ? 2 : index % 4 === 0 ? 1 : 0,
          x: 0, y: 0, previousX: 0, previousY: 0, offsetX: 0, offsetY: 0, vx: 0, vy: 0,
        };
      });
    }

    function updateDust(particle, step, initializing) {
      const drift = Math.sin(time * particle.speed + particle.phase);
      const radius = Math.max(0.008, particle.radius + drift * (0.017 + particle.radius * 0.037));
      const turn = particle.orbital
        ? time * (0.11 + 0.16 / (radius + 0.19))
        : armAngle(radius) + Math.sin(time * 0.19) * 0.24;
      const angle = particle.angle + turn + Math.sin(time * 0.4 + particle.phase + radius * 7) * 0.13;
      const point = project(radius, angle, particle.depth + drift * 0.014);

      if (initializing) {
        particle.x = point.x;
        particle.y = point.y;
        return;
      }

      let fx = -particle.offsetX * 0.021;
      let fy = -particle.offsetY * 0.021;
      if (pointer.opacity > 0.01) {
        const dx = pointer.x - particle.x;
        const dy = pointer.y - particle.y;
        const distance = Math.hypot(dx, dy);
        const influence = 1 - distance / layout.interaction;
        if (influence > 0) {
          const pull = influence * influence * pointer.opacity / Math.max(20, distance);
          const curl = 0.8 + pointer.energy * 1.5;
          fx += (dx * 0.83 - dy * curl) * pull;
          fy += (dy * 0.83 + dx * curl) * pull;
        }
      }

      for (const pulse of pulses) {
        const dx = particle.x - pulse.x;
        const dy = particle.y - pulse.y;
        const distance = Math.hypot(dx, dy);
        const wave = Math.max(0, 1 - Math.abs(distance - pulse.radius) / 60);
        const shock = wave * wave * (1 - pulse.age / pulse.life) * 4.4 / Math.max(14, distance);
        fx += dx * shock;
        fy += dy * shock;
      }

      const drag = 0.92 ** step;
      particle.vx = (particle.vx + fx * step) * drag;
      particle.vy = (particle.vy + fy * step) * drag;
      particle.offsetX += particle.vx * step;
      particle.offsetY += particle.vy * step;
      particle.x = point.x + particle.offsetX;
      particle.y = point.y + particle.offsetY;
    }

    function paintDust(step, initializing = false) {
      const ctx = trails.drawingContext;
      if (!initializing) {
        ctx.globalCompositeOperation = 'destination-out';
        ctx.fillStyle = `rgba(0,0,0,${1 - 0.91 ** step})`;
        ctx.fillRect(0, 0, p.width, p.height);
      }

      for (const bin of trailBins) bin.length = 0;
      for (const particle of dust) {
        particle.previousX = particle.x;
        particle.previousY = particle.y;
        updateDust(particle, step, initializing);
        const flicker = Math.sin(time * 1.4 + particle.phase);
        const light = particle.light === 2 && flicker < -0.40 ? 1 : particle.light;
        trailBins[particle.color * 3 + light].push(particle);
      }

      ctx.globalCompositeOperation = 'lighter';
      ctx.lineCap = 'round';
      for (let i = 0; i < trailBins.length; i++) {
        const light = i % 3;
        ctx.strokeStyle = rgba(palette.colors[Math.floor(i / 3)], [0.12, 0.23, 0.52][light]);
        ctx.lineWidth = [0.62, 0.9, 1.34][light];
        ctx.beginPath();
        for (const { x, y, previousX, previousY } of trailBins[i]) {
          ctx.moveTo(x, y);
          if (initializing) ctx.lineTo(x + 0.55, y);
          else ctx.lineTo(previousX - (x - previousX) * 1.75 + 0.38, previousY - (y - previousY) * 1.75);
        }
        ctx.stroke();
      }
      ctx.globalCompositeOperation = 'source-over';
    }

    function paintBeacons(ctx) {
      for (const star of beacons) {
        const shimmer = 0.63 + Math.sin(time * (0.56 + star.size * 0.3) + star.phase) * 0.29;
        const span = star.size * (0.82 + shimmer * 0.38);
        glow(ctx, star.x, star.y, span * 2.8, star.color, 0.21 * shimmer);
        ctx.fillStyle = rgba(star.color, shimmer * 0.85);
        ctx.fillRect(star.x - 0.62, star.y - 0.62, 1.24, 1.24);
        if (star.size < 2.3) continue;
        ctx.lineWidth = 0.6;
        ctx.strokeStyle = rgba(star.color, shimmer * 0.69);
        ctx.beginPath();
        ctx.moveTo(star.x - span * 0.75, star.y);
        ctx.lineTo(star.x + span * 0.75, star.y);
        ctx.moveTo(star.x, star.y - span);
        ctx.lineTo(star.x, star.y + span);
        ctx.stroke();
      }
    }

    function addPulse(x, y) {
      const sparks = Array.from({ length: 195 }, (_, index) => ({
        theta: p.random(TAU), speed: p.random(44, 320), curl: p.random(-0.72, 0.72),
        length: p.random(0.012, 0.062), size: p.random(0.5, 1.65),
        life: p.random(0.37, 1.44), color: index % 3 === 0 ? index % 2 : 3 + index % 3,
      }));
      pulses.push({ x, y, age: 0, radius: 0, life: 1.48, sparks });
      if (pulses.length > 7) pulses.shift();
      if (paused) p.redraw();
    }

    function paintPulses(ctx) {
      for (const pulse of pulses) {
        // A single still frame represents the burst while motion is paused.
        const age = paused ? Math.max(0.21, pulse.age) : pulse.age;
        const radius = 8 + age * (210 - age * 42);
        const fade = Math.max(0, 1 - age / 1.14) ** 2;
        const core = palette.colors[5];
        glow(ctx, pulse.x, pulse.y, 33 + age * 110, core, fade * 0.65);

        for (let ring = 0; ring < 3; ring++) {
          const ringRadius = radius * (1 - ring * 0.16);
          ctx.strokeStyle = rgba(palette.colors[ring === 1 ? 1 : 4], fade * [0.88, 0.42, 0.22][ring]);
          ctx.lineWidth = [1.1, 0.7, 1.65][ring];
          ctx.beginPath();
          ctx.arc(pulse.x, pulse.y, ringRadius, 0, TAU);
          ctx.stroke();
        }

        for (const spark of pulse.sparks) {
          if (age >= spark.life) continue;
          const earlier = Math.max(0, age - spark.length);
          const distance = spark.speed * (1 - Math.exp(-2.1 * age)) * 0.72;
          const oldDistance = spark.speed * (1 - Math.exp(-2.1 * earlier)) * 0.72;
          const angle = spark.theta + spark.curl * age;
          const oldAngle = spark.theta + spark.curl * earlier;
          ctx.lineWidth = spark.size;
          ctx.strokeStyle = rgba(palette.colors[spark.color], (1 - age / spark.life) ** 1.45);
          ctx.beginPath();
          ctx.moveTo(pulse.x + Math.cos(angle) * distance, pulse.y + Math.sin(angle) * distance);
          ctx.lineTo(pulse.x + Math.cos(oldAngle) * oldDistance, pulse.y + Math.sin(oldAngle) * oldDistance);
          ctx.stroke();
        }
      }
    }

    function paintPointer(ctx) {
      if (pointer.opacity < 0.025 || paused) return;
      const color = palette.colors[2];
      const radius = 12 + pointer.energy * 11;
      glow(ctx, pointer.x, pointer.y, 42 + pointer.energy * 17, color, 0.10 * pointer.opacity);
      ctx.beginPath();
      ctx.arc(pointer.x, pointer.y, radius, 0, TAU);
      ctx.lineWidth = 0.7;
      ctx.strokeStyle = rgba(color, 0.48 * pointer.opacity);
      ctx.stroke();
    }

    function rebuild() {
      backdrop?.remove();
      trails?.remove();
      layout = getLayout(p.width, p.height);
      backdrop = p.createGraphics(p.width, p.height);
      trails = p.createGraphics(p.width, p.height);
      backdrop.pixelDensity(1);
      trails.pixelDensity(1);
      makeBackdrop();
      makeDust();
      paintDust(1, true);
      pulses = [];
      pointer.inside = false;
      pointer.opacity = 0;
    }

    function syncPause() {
      pauseButton.setAttribute('aria-pressed', String(paused));
      pauseButton.setAttribute('aria-label', paused ? '继续星尘' : '暂停星尘');
      if (paused) {
        p.noLoop();
        p.redraw();
      } else p.loop();
    }

    function togglePause() {
      paused = !paused;
      syncPause();
    }

    function movePointer(event) {
      if (!event.isPrimary) return;
      const rect = sky.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      if (pointer.inside) pointer.energy = clamp(pointer.energy + Math.hypot(x - pointer.x, y - pointer.y) * 0.022, 0, 1);
      pointer.x = x;
      pointer.y = y;
      pointer.inside = true;
    }

    async function toggleFullscreen() {
      try {
        if (document.fullscreenElement) await document.exitFullscreen();
        else await document.documentElement.requestFullscreen();
      } catch (error) {
        fullscreenButton.title = '浏览器当前无法切换全屏';
      }
    }

    p.setup = () => {
      p.pixelDensity(Math.min(1.5, window.devicePixelRatio || 1));
      p.createCanvas(sky.clientWidth, sky.clientHeight).parent(sky);
      rebuild();
      syncPause();

      sky.addEventListener('pointermove', movePointer);
      for (const eventName of ['pointerleave', 'pointercancel']) {
        sky.addEventListener(eventName, () => { pointer.inside = false; });
      }
      sky.addEventListener('pointerdown', event => {
        if (!event.isPrimary || event.button !== 0) return;
        movePointer(event);
        addPulse(pointer.x, pointer.y);
      });
      sky.addEventListener('pointerup', event => {
        if (event.pointerType !== 'mouse') pointer.inside = false;
      });

      pauseButton.addEventListener('click', togglePause);
      fullscreenButton.hidden = !document.fullscreenEnabled;
      fullscreenButton.addEventListener('click', toggleFullscreen);
      document.addEventListener('fullscreenchange', () => {
        fullscreenButton.setAttribute('aria-pressed', String(Boolean(document.fullscreenElement)));
        fullscreenButton.setAttribute('aria-label', document.fullscreenElement ? '退出全屏' : '进入全屏');
      });
      document.addEventListener('keydown', event => {
        if (event.repeat || event.ctrlKey || event.altKey || event.metaKey) return;
        if (event.code === 'Space' && !(event.target instanceof HTMLButtonElement)) {
          event.preventDefault();
          togglePause();
        }
        if (event.code === 'KeyF' && !fullscreenButton.hidden) toggleFullscreen();
      });

      for (const swatch of swatches) {
        swatch.addEventListener('click', () => {
          const selected = palettes[swatch.dataset.palette];
          if (palette === selected) return;
          palette = selected;
          document.documentElement.style.setProperty('--accent', palette.accent);
          swatches.forEach(button => button.setAttribute('aria-pressed', String(button === swatch)));
          trails.clear();
          makeBackdrop();
          if (paused) {
            paintDust(1, true);
            p.redraw();
          }
        });
      }
    };

    p.draw = () => {
      if (!paused) {
        const elapsed = clamp(p.deltaTime / 1000 || 1 / 60, 1 / 120, 1 / 24);
        time += elapsed;
        const step = elapsed * 60;
        pointer.opacity = mix(pointer.opacity, Number(pointer.inside), 1 - 0.84 ** step);
        pointer.energy *= 0.89 ** step;
        for (const pulse of pulses) {
          pulse.age += elapsed;
          pulse.radius = 8 + pulse.age * (210 - pulse.age * 42);
        }
        pulses = pulses.filter(pulse => pulse.age < pulse.life);
        paintDust(step);
      }

      const ctx = p.drawingContext;
      ctx.drawImage(backdrop.canvas, 0, 0, p.width, p.height);
      ctx.globalCompositeOperation = 'lighter';
      ctx.drawImage(trails.canvas, 0, 0, p.width, p.height);
      paintBeacons(ctx);
      paintPulses(ctx);
      paintPointer(ctx);
      ctx.globalCompositeOperation = 'source-over';
    };

    p.windowResized = () => {
      const width = sky.clientWidth;
      const height = sky.clientHeight;
      if (p.width === width && p.height === height) return;
      p.resizeCanvas(width, height, true);
      rebuild();
      if (paused) p.redraw();
    };
  });
})();
