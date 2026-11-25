import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';

const { values } = parseArgs({ options: {
  width: { type: 'string', default: '4800' },
  height: { type: 'string' },
  out: { type: 'string', default: 'Chengdu-Financial-City-at-Dusk.png' },
  chrome: { type: 'string' },
  hardware: { type: 'boolean' },
  help: { type: 'boolean' },
} });
if (values.help) {
  console.log('node render.mjs [--width 4800] [--height 3200] [--out image.png] [--chrome /path/to/chrome] [--hardware]');
  process.exit(0);
}
const width = Number(values.width);
const height = Number(values.height ?? Math.round(width * 2 / 3));
if (![width, height].every(n => Number.isInteger(n) && n >= 160 && n <= 8192)) {
  throw new Error('Width and height must be integers between 160 and 8192.');
}

const windows = ['PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'].flatMap(key => {
  const directory = process.env[key];
  return directory ? [join(directory, 'Google/Chrome/Application/chrome.exe'),
    join(directory, 'Microsoft/Edge/Application/msedge.exe')] : [];
});
const chrome = values.chrome ?? process.env.CHROME_PATH ?? [...windows,
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
].find(existsSync);
if (!chrome) throw new Error('Set CHROME_PATH or pass --chrome with the path to Chrome, Chromium or Edge.');

const source = dirname(fileURLToPath(import.meta.url));
const temporary = await mkdtemp(join(tmpdir(), 'chengdu-render-'));
const output = resolve(values.out);
try {
  const scripts = await Promise.all(['shaders.js', 'scene.js', 'renderer.js'].map(name => readFile(join(source, name), 'utf8')));
  const page = join(temporary, 'render.html');
  const html = `<!doctype html><meta charset="utf-8"><canvas id="frame"></canvas><pre id="result"></pre><script>
    ${scripts.join('\n')}
    const result = document.getElementById('result');
    try {
      const data = renderFrame(${width}, ${height});
      result.textContent = data;
    } catch (error) {
      result.textContent = 'RENDER_ERROR: ' + (error.stack || error);
    }
    </script>`;
  await writeFile(page, html);
  console.log(`Rendering ${width} × ${height}…`);
  const args = ['--headless', '--no-sandbox', '--disable-dev-shm-usage', '--disable-background-networking',
    '--no-first-run', '--no-default-browser-check', '--disable-extensions',
    '--disable-gpu-process-crash-limit', '--enable-unsafe-swiftshader', `--user-data-dir=${join(temporary, 'profile')}`];
  if (!values.hardware) args.push('--use-gl=angle', '--use-angle=swiftshader');
  args.push('--dump-dom', pathToFileURL(page).href);
  const child = spawn(chrome, args, { windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
  const chunks = [];
  let diagnostics = '';
  child.stdout.on('data', chunk => chunks.push(chunk));
  child.stderr.on('data', chunk => { diagnostics += chunk.toString(); });
  const code = await new Promise((resolveExit, reject) => {
    child.once('error', reject);
    child.once('close', resolveExit);
  });
  const result = Buffer.concat(chunks).toString('utf8').match(/<pre id="result">(.*?)<\/pre>/s)?.[1];
  const prefix = 'data:image/png;base64,';
  if (code !== 0 || !result?.startsWith(prefix)) {
    throw new Error(result || diagnostics || `Chrome exited with code ${code}.`);
  }
  const image = Buffer.from(result.slice(prefix.length), 'base64');
  if (image.readUInt32BE(16) !== width || image.readUInt32BE(20) !== height) {
    throw new Error('The exported PNG has unexpected dimensions.');
  }
  await writeFile(output, image);
  console.log(`${output} (${(image.length / 1024 / 1024).toFixed(1)} MiB)`);
} finally {
  await rm(temporary, { recursive: true, force: true, maxRetries: 5, retryDelay: 250 });
}
