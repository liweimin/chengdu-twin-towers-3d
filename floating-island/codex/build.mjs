// Run with node build.mjs [path to the esbuild executable].
import {spawnSync} from 'node:child_process';
import {readFile, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';

const root = new URL('./', import.meta.url);
const index = new URL('index.html', root);
const {error, status, stdout, stderr} = spawnSync(process.argv[2] ?? 'esbuild', [
  'scene.js',
  '--bundle',
  '--minify',
  '--format=iife',
  '--legal-comments=inline',
  '--alias:three=./vendor/three.module.min.js',
], {cwd: fileURLToPath(root), encoding: 'utf8', maxBuffer: 4 * 1024 * 1024});
if (error) throw error;
if (status !== 0) throw new Error(stderr || 'esbuild failed');

const [html, css, license] = await Promise.all([
  readFile(index, 'utf8'),
  readFile(new URL('style.css', root), 'utf8'),
  readFile(new URL('vendor/LICENSE', root), 'utf8'),
]);
const styles = '<style id="offline-styles">';
const script = '<script id="offline-scene">';
if (!html.includes(styles) || !html.includes(script)) {
  throw new Error('Offline style and script tags are missing from index.html');
}
const code = `/*! Three.js\n${license.trim()}\n*/
try {
${stdout.trim()}
} catch (error) {
  console.error(error);
  document.querySelector('#status').textContent = '场景加载失败。请使用支持 WebGL 2 的浏览器打开。';
}`;
const result = html
  .replace(/<style id="offline-styles">[\s\S]*?<\/style>/, () => `${styles}\n${css.trim()}\n  </style>`)
  .replace(/<script id="offline-scene">[\s\S]*?<\/script>/, () => `${script}\n${code}\n  </script>`);
await writeFile(index, result, 'utf8');
