// render_film.mjs
// Launches headless Chrome ONCE to stream all 720 animated watercolor frames (1600x900 @ 24fps)
// directly to disk, ready for HD H.264 video + audio mastering!

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';

const ROOT = process.cwd();
const FRAMES_DIR = path.join(ROOT, 'frames');
fs.rmSync(FRAMES_DIR, { recursive: true, force: true });
fs.mkdirSync(FRAMES_DIR, { recursive: true });

const FPS = 24;
const DURATION = 30;
const TOTAL = FPS * DURATION;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.png': 'image/png',
};

let received = 0;
let chromeProc = null;
const t0 = Date.now();

const server = http.createServer((req, res) => {
  const urlObj = new URL(req.url, 'http://127.0.0.1');

  if (req.method === 'POST' && urlObj.pathname === '/frame') {
    const idx = parseInt(urlObj.searchParams.get('i'), 10);
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => {
      const buf = Buffer.concat(chunks);
      const fname = path.join(FRAMES_DIR, `frame_${String(idx).padStart(4, '0')}.jpg`);
      fs.writeFileSync(fname, buf);
      received++;
      if (received % 48 === 0 || received === TOTAL) {
        const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
        console.log(`Rendered ${received}/${TOTAL} frames (${elapsed}s)`);
      }
      res.writeHead(200);
      res.end('ok');
    });
    return;
  }

  if (req.method === 'POST' && urlObj.pathname === '/done') {
    res.writeHead(200);
    res.end('bye');
    console.log(`All ${received} frames rendered in ${((Date.now() - t0) / 1000).toFixed(1)}s!`);
    if (chromeProc) chromeProc.kill();
    server.close();
    return;
  }

  if (req.method === 'POST' && urlObj.pathname === '/error') {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => {
      console.error('Browser error:', Buffer.concat(chunks).toString());
      res.writeHead(200);
      res.end('logged');
      if (chromeProc) chromeProc.kill();
      server.close();
      process.exit(1);
    });
    return;
  }

  const filePath = path.join(ROOT, urlObj.pathname === '/' ? 'animate.html' : urlObj.pathname);
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    res.writeHead(200, { 'Content-Type': MIME[path.extname(filePath)] || 'application/octet-stream' });
    fs.createReadStream(filePath).pipe(res);
  } else {
    res.writeHead(404);
    res.end('Not found');
  }
});

const browser = [
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
].find((p) => fs.existsSync(p));

server.listen(0, '127.0.0.1', () => {
  const port = server.address().port;
  const url = `http://127.0.0.1:${port}/animate.html?fps=${FPS}&duration=${DURATION}`;
  console.log(`Starting headless render (${TOTAL} frames @ ${FPS}fps) via ${browser}`);
  chromeProc = spawn(browser, [
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--no-sandbox',
    '--window-size=1600,900',
    '--remote-debugging-port=0',
    url,
  ], { stdio: 'ignore' });
});
