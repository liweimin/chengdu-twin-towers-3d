// render_keyframes.mjs
// Serves the local directory on an ephemeral localhost port and screenshots all 4 keyframes via headless Chrome

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const ROOT = process.cwd();
const OUT_DIR = path.join(ROOT, 'keyframes');
fs.mkdirSync(OUT_DIR, { recursive: true });

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.png': 'image/png',
};

const server = http.createServer((req, res) => {
  const urlPath = (req.url || '/').split('?')[0];
  const filePath = path.join(ROOT, urlPath === '/' ? 'render.html' : urlPath);
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath);
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    fs.createReadStream(filePath).pipe(res);
  } else {
    res.writeHead(404);
    res.end('Not found');
  }
});

const chromeCandidates = [
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
];
const browser = chromeCandidates.find(p => fs.existsSync(p));
if (!browser) {
  console.error('No Chrome or Edge executable found.');
  process.exit(1);
}

const scenes = ['kf1_launch', 'kf2_eddy', 'kf3_nudge', 'kf4_sunlight'];

server.listen(0, '127.0.0.1', async () => {
  const port = server.address().port;
  console.log(`Using browser: ${browser}`);
  console.log(`Static server on http://127.0.0.1:${port}`);

  try {
    for (const scene of scenes) {
      const outPath = path.join(OUT_DIR, `${scene}.png`);
      const url = `http://127.0.0.1:${port}/render.html?scene=${scene}`;
      console.log(`Rendering ${scene}...`);
      await execFileAsync(browser, [
        '--headless=new',
        '--disable-gpu',
        '--hide-scrollbars',
        '--force-device-scale-factor=1',
        '--window-size=1600,900',
        '--virtual-time-budget=4000',
        `--screenshot=${outPath}`,
        url,
      ], { timeout: 60000 });

      const sizeKB = (fs.statSync(outPath).size / 1024).toFixed(1);
      console.log(`Saved ${outPath} (${sizeKB} KB)`);
    }
  } finally {
    server.close();
  }
});
