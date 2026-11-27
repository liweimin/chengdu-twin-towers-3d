// render_single.mjs
// Fast single-scene renderer for rapid visual self-critique and iteration
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const ROOT = process.cwd();
const scene = process.argv[2] || 'child_study';
const outFile = process.argv[3] || path.join(ROOT, 'keyframes', `${scene}.png`);
fs.mkdirSync(path.dirname(outFile), { recursive: true });

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.png': 'image/png',
};

const server = http.createServer((req, res) => {
  const urlPath = (req.url || '/').split('?')[0];
  const filePath = path.join(ROOT, urlPath === '/' ? 'render.html' : urlPath);
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
].find(p => fs.existsSync(p));

server.listen(0, '127.0.0.1', async () => {
  const port = server.address().port;
  try {
    await execFileAsync(browser, [
      '--headless=new',
      '--disable-gpu',
      '--hide-scrollbars',
      '--force-device-scale-factor=1',
      '--window-size=1600,900',
      '--virtual-time-budget=3000',
      `--screenshot=${outFile}`,
      `http://127.0.0.1:${port}/render.html?scene=${scene}`,
    ], { timeout: 60000 });
    console.log(`Rendered ${scene} -> ${outFile} (${(fs.statSync(outFile).size / 1024).toFixed(1)} KB)`);
  } finally {
    server.close();
  }
});
