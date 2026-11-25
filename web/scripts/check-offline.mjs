// Fails the build if the bundle would load anything from outside the deployment (no CDN, no map tiles, no external
// fonts). Run after `vite build` (npm run build does). HTML and CSS: no absolute http(s) URL at all, except XML
// namespaces. JavaScript: no import, fetch, worker, socket, script or stylesheet pointed at an absolute URL. Other
// URL strings inside libraries (documentation links in error messages) are listed but are not network loads.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { extname, join } from "node:path";

const DIST = new URL("../dist/", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
const NAMESPACES = /^https?:\/\/(www\.w3\.org|www\.w3\.org\/1999\/xlink|www\.w3\.org\/2000\/svg)/;
const LOADS = [
  /\bimport\s*\(\s*["'`](https?:)?\/\//,
  /\bfrom\s*["'](https?:)?\/\//,
  /\bfetch\s*\(\s*["'`](https?:)?\/\//,
  /\bnew\s+(Worker|SharedWorker|WebSocket|EventSource)\s*\(\s*["'`](https?|wss?):\/\//,
  /\bimportScripts\s*\(\s*["'`]https?:/,
  /\.src\s*=\s*["'`]https?:\/\//,
  /<(script|link|img|iframe)[^>]+(src|href)\s*=\s*["']?(https?:)?\/\//i,
  /@import\s+(url\()?["']?(https?:)?\/\//,
  /url\(\s*["']?(https?:)?\/\//,
];

function files(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? files(path) : [path];
  });
}

const failures = [];
const mentioned = new Set();
for (const path of files(DIST)) {
  const ext = extname(path);
  if (![".html", ".css", ".js", ".mjs", ".svg"].includes(ext)) continue;
  const text = readFileSync(path, "utf8");
  for (const pattern of LOADS) {
    const m = text.match(pattern);
    if (m) failures.push(`${path}: ${m[0].slice(0, 120)}`);
  }
  if (ext === ".html" || ext === ".css") {
    for (const m of text.matchAll(/https?:\/\/[^\s"'<>)]+/g)) {
      if (!NAMESPACES.test(m[0])) failures.push(`${path}: ${m[0]}`);
    }
  } else {
    for (const m of text.matchAll(/https?:\/\/[A-Za-z0-9.-]+/g)) mentioned.add(m[0]);
  }
}
if (mentioned.size) console.log(`URL strings inside bundled libraries (not loads): ${[...mentioned].sort().join(", ")}`);
if (failures.length) {
  console.error(`External network assets in the built bundle:\n  ${failures.join("\n  ")}`);
  process.exit(1);
}
console.log("check-offline: no external network asset in dist/");
