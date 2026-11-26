import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const HTML_PATH = path.join(__dirname, 'animation.html');
const AUDIO_PATH = path.join(__dirname, 'soundtrack.wav');
const OUTPUT_MP4 = path.join(__dirname, 'paper_boat_story.mp4');
const PREVIEW_DIR = path.join(__dirname, 'preview_frames');

const PREVIEW_FRAME_INDICES = new Set([18, 48, 125, 195, 268, 345]);

function findChromeBinary() {
  const candidates = [
    process.env.CHROME_PATH,
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ].filter(Boolean);
  for (const p of candidates) {
    if (fs.existsSync(p)) return p;
  }
  throw new Error('Could not find Chrome or Edge binary. Set CHROME_PATH env variable.');
}

function startStaticServer() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const urlPath = (req.url || '/').split('?')[0];
      if (urlPath === '/' || urlPath === '/animation.html') {
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        fs.createReadStream(HTML_PATH).pipe(res);
      } else {
        res.writeHead(404);
        res.end('Not found');
      }
    });
    server.listen(0, '127.0.0.1', () => {
      const addr = server.address();
      resolve({ server, url: `http://127.0.0.1:${addr.port}/animation.html?headless=1` });
    });
  });
}

async function waitForDevTools(port, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/json/list`);
      if (res.ok) {
        const list = await res.json();
        const page = list.find((t) => t.type === 'page' && t.webSocketDebuggerUrl);
        if (page) return page.webSocketDebuggerUrl;
      }
    } catch {
      // retry
    }
    await new Promise((r) => setTimeout(r, 120));
  }
  throw new Error('Timed out waiting for Chrome DevTools Protocol');
}

class CDPClient {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.nextId = 1;
    this.pending = new Map();
    this.events = new Map();
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.wsUrl);
      this.ws.addEventListener('open', () => resolve());
      this.ws.addEventListener('error', (err) => reject(err));
      this.ws.addEventListener('message', (ev) => {
        const msg = JSON.parse(ev.data.toString());
        if (msg.id && this.pending.has(msg.id)) {
          const { resolve, reject } = this.pending.get(msg.id);
          this.pending.delete(msg.id);
          if (msg.error) reject(new Error(msg.error.message));
          else resolve(msg.result);
        } else if (msg.method && this.events.has(msg.method)) {
          for (const cb of this.events.get(msg.method)) cb(msg.params);
        }
      });
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  once(method) {
    return new Promise((resolve) => {
      if (!this.events.has(method)) this.events.set(method, new Set());
      const wrapper = (params) => {
        this.events.get(method).delete(wrapper);
        resolve(params);
      };
      this.events.get(method).add(wrapper);
    });
  }

  close() {
    if (this.ws) this.ws.close();
  }
}

async function main() {
  const savePreviews = process.argv.includes('--previews');
  if (savePreviews) fs.mkdirSync(PREVIEW_DIR, { recursive: true });

  const chromePath = findChromeBinary();
  const { server, url } = await startStaticServer();
  const debugPort = 9222 + Math.floor(Math.random() * 500);
  const userDataDir = path.join(__dirname, '.chrome_render_profile');
  fs.rmSync(userDataDir, { recursive: true, force: true });

  console.log(`[render] Launching headless Chrome: ${chromePath}`);
  const chrome = spawn(
    chromePath,
    [
      '--headless=new',
      '--disable-gpu-sandbox',
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-background-timer-throttling',
      '--window-size=1920,1080',
      `--remote-debugging-port=${debugPort}`,
      `--user-data-dir=${userDataDir}`,
      'about:blank',
    ],
    { stdio: 'ignore' }
  );

  let cdp;
  try {
    const wsUrl = await waitForDevTools(debugPort);
    cdp = new CDPClient(wsUrl);
    await cdp.connect();
    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    await cdp.send('Emulation.setDeviceMetricsOverride', {
      width: 1920,
      height: 1080,
      deviceScaleFactor: 1,
      mobile: false,
    });

    const loadDone = cdp.once('Page.loadEventFired');
    await cdp.send('Page.navigate', { url });
    await loadDone;

    const metaRes = await cdp.send('Runtime.evaluate', {
      expression: 'JSON.stringify(window.ANIM_META)',
      returnByValue: true,
    });
    const meta = JSON.parse(metaRes.result.value);
    console.log(`[render] Scene loaded: ${meta.width}x${meta.height} @ ${meta.fps}fps (${meta.totalFrames} frames, ${meta.duration}s)`);

    // Spawn FFmpeg to receive high-quality JPEG frames on stdin and mux with soundtrack.wav if present
    const hasAudio = fs.existsSync(AUDIO_PATH);
    const ffmpegArgs = [
      '-y',
      '-f', 'image2pipe',
      '-vcodec', 'mjpeg',
      '-r', String(meta.fps),
      '-i', '-',
      ...(hasAudio ? ['-i', AUDIO_PATH] : []),
      '-c:v', 'libx264',
      '-preset', 'medium',
      '-crf', '18',
      '-pix_fmt', 'yuv420p',
      '-movflags', '+faststart',
      ...(hasAudio ? ['-c:a', 'aac', '-b:a', '192k', '-shortest'] : []),
      OUTPUT_MP4,
    ];

    console.log(`[render] Spawning FFmpeg (${hasAudio ? 'with soundtrack.wav' : 'video-only'})...`);
    const ffmpeg = spawn('ffmpeg', ffmpegArgs, { stdio: ['pipe', 'ignore', 'pipe'] });
    let ffmpegErr = '';
    ffmpeg.stderr.on('data', (chunk) => {
      ffmpegErr += chunk.toString();
    });

    const startTime = Date.now();
    for (let i = 0; i < meta.totalFrames; i++) {
      const frameRes = await cdp.send('Runtime.evaluate', {
        expression: `(() => { window.renderFrame(${i}); return document.getElementById('stage').toDataURL('image/jpeg', 0.96).slice(23); })()`,
        returnByValue: true,
      });
      const jpgBuf = Buffer.from(frameRes.result.value, 'base64');

      if (savePreviews && PREVIEW_FRAME_INDICES.has(i)) {
        fs.writeFileSync(path.join(PREVIEW_DIR, `frame_${String(i).padStart(3, '0')}.jpg`), jpgBuf);
      }

      if (!ffmpeg.stdin.write(jpgBuf)) {
        await new Promise((r) => ffmpeg.stdin.once('drain', r));
      }

      if ((i + 1) % 50 === 0 || i === meta.totalFrames - 1) {
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        console.log(`[render] Frame ${i + 1}/${meta.totalFrames} (${elapsed}s)`);
      }
    }

    ffmpeg.stdin.end();
    const exitCode = await new Promise((resolve) => ffmpeg.on('close', resolve));
    if (exitCode !== 0) {
      throw new Error(`FFmpeg failed with exit code ${exitCode}:\n${ffmpegErr}`);
    }
    console.log(`[render] Successfully created ${OUTPUT_MP4}`);
  } finally {
    if (cdp) cdp.close();
    chrome.kill();
    server.close();
    setTimeout(() => fs.rmSync(userDataDir, { recursive: true, force: true }), 400);
  }
}

main().catch((err) => {
  console.error('[render] ERROR:', err);
  process.exit(1);
});
