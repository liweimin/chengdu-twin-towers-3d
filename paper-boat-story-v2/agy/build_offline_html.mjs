// build_offline_html.mjs
// Bundles the entire 《纸船的故事》 animated watercolor film + original music/foley/voiceover
// into a single 100% offline, zero-dependency, file://-compatible HTML picture-book cinema!

import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const ROOT = process.cwd();
const AUDIO_WAV = path.join(ROOT, 'audio', 'final_master.wav');
const AUDIO_MP3 = path.join(ROOT, 'audio', 'final_master.mp3');
const OUT_HTML = path.join(ROOT, '纸船的故事_离线绘本影院.html');

// 1. Compress mastered 30s stereo audio to crisp 128kbps MP3 for lightweight single-file embedding
console.log('Encoding audio to 128kbps MP3...');
execFileSync('ffmpeg', [
  '-y', '-i', AUDIO_WAV,
  '-c:a', 'libmp3lame', '-b:a', '128k', '-ar', '44100', '-ac', '2',
  AUDIO_MP3,
], { stdio: 'pipe' });

const mp3Base64 = fs.readFileSync(AUDIO_MP3).toString('base64');
console.log(`Audio MP3 size: ${(fs.statSync(AUDIO_MP3).size / 1024).toFixed(1)} KB`);

// 2. Read & inline our 3 core watercolor animation modules (stripping ES module import/export for file:// compatibility!)
function stripModuleSyntax(code) {
  return code
    .replace(/^\s*import\s+[\s\S]*?from\s+['"][^'"]+['"];?\s*$/gm, '')
    .replace(/^\s*export\s+(?=(class|function|const|let|var)\b)/gm, '');
}

const wcCode = stripModuleSyntax(fs.readFileSync(path.join(ROOT, 'watercolor_v2.js'), 'utf8'));
const charCode = stripModuleSyntax(fs.readFileSync(path.join(ROOT, 'characters_v2.js'), 'utf8'));
let animCode = stripModuleSyntax(fs.readFileSync(path.join(ROOT, 'animate_scenes.js'), 'utf8'));

// 3. Upgrade PaperBoatFilm in the offline real-time player to use a GPU-accelerated cached
//    Arches 300gsm cold-press paper overlay so playback runs effortlessly at smooth 30-60fps!
const gpuPaperReplacement = `
  _precomputePaperLUT() {
    const w = this.w, h = this.h;
    this.paperOverlay = document.createElement('canvas');
    this.paperOverlay.width = w;
    this.paperOverlay.height = h;
    const pctx = this.paperOverlay.getContext('2d');
    const img = pctx.createImageData(w, h);
    const d = img.data;
    const dummy = document.createElement('canvas');
    dummy.width = 4; dummy.height = 4;
    const st = new WatercolorStudio(dummy, 2026);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const dimple = st.noise1.fbm(x * 0.085, y * 0.085, 3);
        const fine = st.noise2.sample(x * 0.34, y * 0.34);
        const tooth = dimple * 0.65 + fine * 0.35;
        const v = Math.max(0, Math.min(255, Math.round(244 + (tooth - 0.5) * 28)));
        const p = (y * w + x) * 4;
        d[p] = v;
        d[p + 1] = Math.round(v * 0.996);
        d[p + 2] = Math.round(v * 0.985);
        d[p + 3] = 255;
      }
    }
    pctx.putImageData(img, 0, 0);
  }

  _applyFastPaperPhysics(canvas, warmth = 0.06) {
    const w = this.w, h = this.h;
    const ctx = canvas.getContext('2d');
    // Hardware-accelerated cold-press Arches paper grain overlay
    ctx.save();
    ctx.globalCompositeOperation = 'multiply';
    ctx.globalAlpha = 0.85;
    ctx.drawImage(this.paperOverlay, 0, 0);
    ctx.restore();

    if (warmth > 0) {
      ctx.save();
      ctx.globalCompositeOperation = 'soft-light';
      ctx.fillStyle = \`rgba(255, 240, 200, \${warmth})\`;
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
`;

// Replace _precomputePaperLUT() { ... } and _applyFastPaperPhysics() { ... } method bodies cleanly
animCode = animCode.replace(
  /\n  _precomputePaperLUT\(\) \{[\s\S]*?\n  _buildShotCaches\(\) \{/,
  '\n' + gpuPaperReplacement + '\n  _buildShotCaches() {'
);

const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>纸船的故事 · 水彩绘本动画短片</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      min-height: 100vh;
      background: radial-gradient(circle at 50% 35%, #FAF5E8 0%, #EFE6D3 100%);
      color: #4F3D31;
      font-family: "STKaiti", "KaiTi", "PingFang SC", "Microsoft YaHei", Georgia, serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
      user-select: none;
    }
    .book-frame {
      width: min(94vw, 1180px);
      background: #FCF9F1;
      border-radius: 14px;
      padding: 14px 14px 16px;
      box-shadow: 0 22px 60px rgba(74, 56, 40, 0.16), 0 4px 16px rgba(74, 56, 40, 0.08);
      border: 1px solid rgba(168, 144, 112, 0.28);
    }
    .stage-wrap {
      position: relative;
      width: 100%;
      aspect-ratio: 16 / 9;
      border-radius: 8px;
      overflow: hidden;
      background: #FCF9F1;
      cursor: pointer;
    }
    canvas {
      display: block;
      width: 100%;
      height: 100%;
    }
    .cover-overlay {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: rgba(252, 249, 241, 0.32);
      backdrop-filter: blur(2px);
      transition: opacity 0.55s ease, visibility 0.55s ease;
    }
    .cover-overlay.hidden {
      opacity: 0;
      visibility: hidden;
      pointer-events: none;
    }
    .play-pill {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px 30px;
      border-radius: 999px;
      border: 1.5px solid rgba(110, 82, 62, 0.35);
      background: rgba(255, 253, 247, 0.92);
      color: #543D2E;
      font-size: 20px;
      font-family: inherit;
      letter-spacing: 2px;
      cursor: pointer;
      box-shadow: 0 10px 28px rgba(84, 61, 46, 0.16);
      transition: transform 0.2s ease, background 0.2s ease;
    }
    .play-pill:hover {
      transform: translateY(-2px) scale(1.02);
      background: #FFFFFF;
    }
    .play-icon {
      width: 0; height: 0;
      border-top: 9px solid transparent;
      border-bottom: 9px solid transparent;
      border-left: 15px solid #5C8DC4;
      margin-left: 3px;
    }
    .controls {
      margin-top: 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 2px 6px;
    }
    .timeline-row {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .btn {
      border: 1px solid rgba(130, 105, 84, 0.28);
      background: #FFFDF8;
      color: #543D2E;
      border-radius: 8px;
      padding: 6px 13px;
      font-size: 14px;
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
      cursor: pointer;
      transition: background 0.15s ease;
    }
    .btn:hover { background: #F5ECD9; }
    .scrubber {
      flex: 1;
      height: 6px;
      accent-color: #588DC9;
      cursor: pointer;
    }
    .timecode {
      font-size: 13px;
      font-family: ui-monospace, Consolas, monospace;
      color: #7D6857;
      min-width: 92px;
      text-align: right;
    }
    .chapters {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      flex-wrap: wrap;
    }
    .chapter-btn {
      flex: 1;
      min-width: 130px;
      text-align: center;
      padding: 5px 8px;
      border-radius: 6px;
      border: 1px solid transparent;
      background: rgba(235, 224, 202, 0.42);
      color: #6B5748;
      font-size: 13px;
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .chapter-btn:hover { background: rgba(220, 206, 178, 0.65); }
    .chapter-btn.active {
      background: rgba(88, 141, 201, 0.16);
      border-color: rgba(88, 141, 201, 0.45);
      color: #385E8C;
      font-weight: 600;
    }
    .subtitle {
      margin-top: 10px;
      font-size: 13px;
      color: #8C7766;
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
      letter-spacing: 0.5px;
    }
  </style>
</head>
<body>
  <div class="book-frame">
    <div class="stage-wrap" id="stageWrap">
      <canvas id="stage" width="1600" height="900"></canvas>
      <div class="cover-overlay" id="cover">
        <button class="play-pill" id="coverPlayBtn">
          <span class="play-icon"></span>
          <span>播放《纸船的故事》</span>
        </button>
      </div>
    </div>

    <div class="controls">
      <div class="timeline-row">
        <button class="btn" id="playBtn">播放</button>
        <button class="btn" id="replayBtn">重播</button>
        <input class="scrubber" id="scrubber" type="range" min="0" max="30" step="0.02" value="0" />
        <span class="timecode" id="timecode">00:00 / 00:30</span>
        <button class="btn" id="muteBtn">声音：开</button>
        <button class="btn" id="fsBtn">全屏</button>
      </div>
      <div class="chapters">
        <button class="chapter-btn active" data-t="0.0">一 · 入水与启程 (00:00)</button>
        <button class="chapter-btn" data-t="7.5">二 · 林荫小停顿 (00:07)</button>
        <button class="chapter-btn" data-t="14.5">三 · 偶遇与轻推 (00:14)</button>
        <button class="chapter-btn" data-t="22.5">四 · 驶向阳光 (00:22)</button>
      </div>
    </div>
  </div>
  <div class="subtitle">纯代码程序化水彩绘本短片 · 含原创配乐、自然音效与中文旁白 · 100% 离线单文件可播</div>

  <audio id="bgm" preload="auto" src="data:audio/mpeg;base64,${mp3Base64}"></audio>

  <script>
  (function() {
    'use strict';

    // === 1. Watercolor Studio Engine ===
    ${wcCode}

    // === 2. Storybook Watercolor Characters & Props ===
    ${charCode}

    // === 3. 30s Animated Watercolor Film Engine ===
    ${animCode}

    // === 4. Interactive Offline Picture-Book Cinema Controller ===
    const DURATION = 30.0;
    const canvas = document.getElementById('stage');
    const audio = document.getElementById('bgm');
    const cover = document.getElementById('cover');
    const coverPlayBtn = document.getElementById('coverPlayBtn');
    const playBtn = document.getElementById('playBtn');
    const replayBtn = document.getElementById('replayBtn');
    const muteBtn = document.getElementById('muteBtn');
    const fsBtn = document.getElementById('fsBtn');
    const scrubber = document.getElementById('scrubber');
    const timecode = document.getElementById('timecode');
    const stageWrap = document.getElementById('stageWrap');
    const chapterBtns = Array.from(document.querySelectorAll('.chapter-btn'));

    const film = new PaperBoatFilm(1600, 900);

    let isPlaying = false;
    let currentTime = 2.4; // Show charming cover frame (child launching boat) before play!
    let rafId = null;
    let lastPerf = 0;

    function fmtTime(sec) {
      const s = Math.max(0, Math.min(DURATION, sec));
      const mm = String(Math.floor(s / 60)).padStart(2, '0');
      const ss = String(Math.floor(s % 60)).padStart(2, '0');
      return mm + ':' + ss + ' / 00:30';
    }

    function updateChapterHighlight(t) {
      let idx = 0;
      if (t >= 22.5) idx = 3;
      else if (t >= 14.5) idx = 2;
      else if (t >= 7.5) idx = 1;
      chapterBtns.forEach((b, i) => b.classList.toggle('active', i === idx));
    }

    function drawAt(t) {
      const clamped = Math.max(0, Math.min(DURATION, t));
      film.renderFrame(canvas, clamped);
      scrubber.value = clamped.toFixed(2);
      timecode.textContent = fmtTime(clamped);
      updateChapterHighlight(clamped);
    }

    // Draw initial charming cover preview immediately!
    drawAt(2.35);

    function tick(now) {
      if (!isPlaying) return;
      if (!audio.paused && !audio.ended) {
        currentTime = audio.currentTime;
      } else {
        const dt = (now - lastPerf) / 1000;
        currentTime += Math.min(0.1, dt);
      }
      lastPerf = now;

      if (currentTime >= DURATION) {
        currentTime = DURATION;
        drawAt(DURATION);
        pauseFilm();
        cover.classList.remove('hidden');
        coverPlayBtn.querySelector('span:last-child').textContent = '重新播放《纸船的故事》';
        return;
      }

      drawAt(currentTime);
      rafId = requestAnimationFrame(tick);
    }

    function playFilm(startAt = null) {
      if (startAt !== null) {
        currentTime = startAt;
        audio.currentTime = startAt;
      } else if (currentTime >= DURATION - 0.1 || cover.classList.contains('hidden') === false && currentTime === 2.35) {
        currentTime = 0;
        audio.currentTime = 0;
      } else {
        audio.currentTime = currentTime;
      }
      cover.classList.add('hidden');
      isPlaying = true;
      playBtn.textContent = '暂停';
      lastPerf = performance.now();
      audio.play().catch(() => {});
      if (rafId) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(tick);
    }

    function pauseFilm() {
      isPlaying = false;
      playBtn.textContent = '播放';
      audio.pause();
      if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
    }

    coverPlayBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      playFilm(0);
    });

    stageWrap.addEventListener('click', () => {
      if (isPlaying) pauseFilm();
      else playFilm();
    });

    playBtn.addEventListener('click', () => {
      if (isPlaying) pauseFilm();
      else playFilm();
    });

    replayBtn.addEventListener('click', () => playFilm(0));

    muteBtn.addEventListener('click', () => {
      audio.muted = !audio.muted;
      muteBtn.textContent = audio.muted ? '声音：关' : '声音：开';
    });

    fsBtn.addEventListener('click', () => {
      if (!document.fullscreenElement) stageWrap.requestFullscreen?.();
      else document.exitFullscreen?.();
    });

    scrubber.addEventListener('input', () => {
      const t = parseFloat(scrubber.value);
      currentTime = t;
      audio.currentTime = t;
      cover.classList.add('hidden');
      drawAt(t);
    });

    chapterBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        const t = parseFloat(btn.dataset.t);
        playFilm(t);
      });
    });

    window.__filmReady = true;
  })();
  </script>
</body>
</html>
`;

fs.writeFileSync(OUT_HTML, html, 'utf8');
const totalKB = (fs.statSync(OUT_HTML).size / 1024).toFixed(1);
console.log(`Built standalone offline single-HTML cinema: ${OUT_HTML} (${totalKB} KB)`);
