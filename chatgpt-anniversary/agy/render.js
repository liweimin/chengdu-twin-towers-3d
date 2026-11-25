// High-Speed Parallel 1920x1080 30fps Renderer (6 Chrome workers + canvas.toDataURL + FFmpeg)
const puppeteer = require('puppeteer-core');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const FPS = 30;
const DURATION = 50.0;
const TOTAL_FRAMES = Math.round(FPS * DURATION); // 1500 frames
const WORKERS = 6;

const CHROME_CANDIDATES = [
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
];

function findBrowser() {
  for (const p of CHROME_CANDIDATES) {
    if (fs.existsSync(p)) return p;
  }
  throw new Error('No Chrome/Edge executable found');
}

async function main() {
  const browserPath = findBrowser();
  const sceneUrl = 'file:///' + path.join(__dirname, 'scene.html').replace(/\\/g, '/');
  const audioPath = path.join(__dirname, 'soundtrack.wav');
  const outPath = path.join(__dirname, 'chatgpt_4th_anniversary_tribute.mp4');
  const tmpDir = path.join(__dirname, 'frames_tmp');
  const previewDir = path.join(__dirname, 'preview_frames');

  if (!fs.existsSync(tmpDir)) fs.mkdirSync(tmpDir);
  if (!fs.existsSync(previewDir)) fs.mkdirSync(previewDir);

  const keyFramesToSave = new Set([45, 150, 260, 380, 560, 720, 960, 1140, 1380]);

  console.log(`Launching ${WORKERS} parallel workers using ${browserPath}...`);
  const t0 = Date.now();
  let completed = 0;

  // Launch separate lightweight browser contexts / instances in parallel
  const browsers = await Promise.all(
    Array.from({ length: WORKERS }, () =>
      puppeteer.launch({
        executablePath: browserPath,
        headless: 'new',
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--window-size=1920,1080',
          '--force-device-scale-factor=1',
        ],
      })
    )
  );

  const chunkSize = Math.ceil(TOTAL_FRAMES / WORKERS);

  await Promise.all(
    browsers.map(async (browser, wIdx) => {
      const start = wIdx * chunkSize;
      const end = Math.min(TOTAL_FRAMES, start + chunkSize);
      const page = await browser.newPage();
      await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
      await page.goto(sceneUrl, { waitUntil: 'load' });

      for (let f = start; f < end; f++) {
        const b64 = await page.evaluate((frame, fps) => {
          window.renderFrame(frame, fps);
          return document.getElementById('c').toDataURL('image/jpeg', 0.94).slice(23);
        }, f, FPS);

        const buf = Buffer.from(b64, 'base64');
        const fname = `f_${String(f).padStart(5, '0')}.jpg`;
        fs.writeFileSync(path.join(tmpDir, fname), buf);

        if (keyFramesToSave.has(f)) {
          fs.writeFileSync(path.join(previewDir, `frame_${String(f).padStart(4, '0')}.jpg`), buf);
        }

        completed++;
        if (completed % 150 === 0 || completed === TOTAL_FRAMES) {
          const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
          const pct = ((completed / TOTAL_FRAMES) * 100).toFixed(1);
          console.log(`Rendered ${completed}/${TOTAL_FRAMES} (${pct}%) — ${elapsed}s`);
        }
      }
      await browser.close();
    })
  );

  const renderSecs = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`All ${TOTAL_FRAMES} frames rendered in ${renderSecs}s! Encoding MP4 with FFmpeg...`);

  await new Promise((resolve, reject) => {
    const ff = spawn('ffmpeg', [
      '-y',
      '-framerate', String(FPS),
      '-i', path.join(tmpDir, 'f_%05d.jpg'),
      '-i', audioPath,
      '-c:v', 'libx264',
      '-preset', 'medium',
      '-crf', '18',
      '-pix_fmt', 'yuv420p',
      '-c:a', 'aac',
      '-b:a', '256k',
      '-shortest',
      '-movflags', '+faststart',
      outPath
    ], { stdio: ['ignore', 'inherit', 'pipe'] });

    let err = '';
    ff.stderr.on('data', d => { err += d.toString(); });
    ff.on('close', code => {
      if (code === 0) resolve();
      else reject(new Error(`FFmpeg failed (${code}):\n${err.slice(-1500)}`));
    });
  });

  // Clean up temp frames
  fs.rmSync(tmpDir, { recursive: true, force: true });

  const stats = fs.statSync(outPath);
  const totalSecs = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`SUCCESS! ${outPath} (${(stats.size / 1024 / 1024).toFixed(2)} MB) in ${totalSecs}s`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
