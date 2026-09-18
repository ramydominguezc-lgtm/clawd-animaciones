// Monta un componente compilado (modulo de React + GSAP sacado de un chunk de
// Next.js) en Chrome con el GSAP real, congela la linea de tiempo global y guarda
// el SVG de cada instante. Es el paso 2 de la Parte A2 del metodo; el paso 3 es
// `transcribir_svg.py`.
//
// uso: node capturar_gsap.js <modulo.js> <salida_dir> <ancho_escenario_px> <dt_s | [instantes]> <duracion_s> [props_json]
//
// Requisitos:
//   puppeteer-core           ya instalado en scripts/node_modules (package.json aqui mismo).
//                            Si falta: `npm install` dentro de scripts/
//   Chrome instalado en C:/Program Files/Google/Chrome/Application/chrome.exe
//   gsap.min.js junto a este archivo: GSAP 3.14.2, la version que usaba la demo.
//   Si la fuente usa otra version, bajar esa (cdn.jsdelivr.net/npm/gsap@X/dist/gsap.min.js).
//
// Lo que resuelve: el ancho del escenario importa si el componente mide su
// contenedor (el paseo calcula el recorrido con getBoundingClientRect).
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

const [modulo, salida, anchoEsc, dt, dur, propsJson] = process.argv.slice(2);
const codigo = fs.readFileSync(modulo, 'utf8');
// el cuerpo es el bloque {...} balanceado que sigue a "t=>" (el archivo puede traer basura al final)
const cuerpo = (() => {
  const i = codigo.indexOf('t=>') + 3;
  let d = 0, enStr = null;
  for (let k = i; k < codigo.length; k++) {
    const c = codigo[k];
    if (enStr) { if (c === '\\') k++; else if (c === enStr) enStr = null; continue; }
    if (c === '"' || c === "'" || c === '`') { enStr = c; continue; }
    if (c === '{') d++;
    else if (c === '}' && --d === 0) return codigo.slice(i, k + 1);
  }
})();
fs.mkdirSync(salida, { recursive: true });

const html = `<!doctype html><html><body style="margin:0">
<div id="esc" style="position:relative;width:${anchoEsc}px;padding:200px 0"></div>
<script>${fs.readFileSync(path.join(__dirname, 'gsap.min.js'), 'utf8')}</script>
<script>
const SVGNS = 'http://www.w3.org/2000/svg';
const Fragment = Symbol('frag');
const efectos = [];
const react = { useRef: v => ({ current: v }), useEffect: fn => efectos.push(fn) };
const kebab = k => (k === 'viewBox' ? k : k.replace(/[A-Z]/g, m => '-' + m.toLowerCase()));
function jsx(type, props) { return { type, props: props || {} }; }
function crear(n) {
  if (n == null || n === false) return [];
  if (Array.isArray(n)) return n.flatMap(crear);
  if (typeof n !== 'object') return [document.createTextNode(String(n))];
  if (n.type === Fragment) return crear(n.props.children);
  if (typeof n.type === 'function') return crear(n.type(n.props));
  const el = document.createElementNS(SVGNS, n.type);
  for (const [k, v] of Object.entries(n.props)) {
    if (k === 'children' || k === 'key') continue;
    if (k === 'ref') continue;
    if (k === 'className') { el.setAttribute('class', v); continue; }
    if (k === 'style') { if (v) Object.assign(el.style, v); continue; }
    el.setAttribute(kebab(k), v);
  }
  crear(n.props.children).forEach(c => el.appendChild(c));
  const r = n.props.ref;
  if (typeof r === 'function') r(el); else if (r) r.current = el;
  return [el];
}
let exportado;
const t = {
  i: id => id === 843476 ? { jsx, jsxs: jsx, Fragment } : id === 271645 ? react : { default: gsap },
  s: arr => { const i = arr.indexOf('default'); exportado = arr[i + 1](); },
};
new Function('t', ${JSON.stringify(cuerpo)})(t);
const arbol = exportado(${propsJson || '{}'});
const esc = document.getElementById('esc');
crear(arbol).forEach(el => esc.appendChild(el));
const svg = esc.querySelector('svg');
const vb = svg.getAttribute('viewBox').split(' ').map(Number);
svg.removeAttribute('class');
svg.style.width = vb[2] + 'px'; svg.style.height = vb[3] + 'px'; svg.style.overflow = 'visible';
svg.style.display = 'block';
gsap.ticker.lagSmoothing(0);
efectos.forEach(fn => fn());
gsap.globalTimeline.pause();
const T0 = gsap.globalTimeline.time();
window.ir = s => { gsap.globalTimeline.seek(T0 + s, false); return svg.outerHTML; };
// modo geometria: cada rect visible como cuadrilatero en unidades del viewBox,
// en orden de pintado, con el rectangulo de recorte que le toque (si hay).
window.poligonos = s => {
  gsap.globalTimeline.seek(T0 + s, false);
  const inv = svg.getScreenCTM().inverse();
  const esquinas = (el, m) => {
    const x = +el.getAttribute('x') || 0, y = +el.getAttribute('y') || 0;
    const w = +el.getAttribute('width'), h = +el.getAttribute('height');
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
      .map(([px, py]) => { const p = new DOMPoint(px, py).matrixTransform(m); return [p.x, p.y]; });
  };
  const out = [];
  for (const el of svg.querySelectorAll('rect')) {
    if (el.closest('defs')) continue;
    let oculto = false, recorte = null;
    for (let n = el; n && n !== svg; n = n.parentNode) {
      if (getComputedStyle(n).display === 'none') oculto = true;
      const cp = n.getAttribute && n.getAttribute('clip-path');
      if (cp && !recorte) {
        const r = document.querySelector(cp.replace(/^url\\((.*)\\)$/, '$1') + ' rect');
        if (r) recorte = esquinas(r, inv.multiply(n.getScreenCTM()));
      }
    }
    if (oculto) continue;
    out.push({ id: el.id || '', fill: el.getAttribute('fill'), pts: esquinas(el, inv.multiply(el.getScreenCTM())), recorte });
  }
  // ancla: traslacion del grupo que mueve al personaje entero (id en ANCLA),
  // para redondear ese movimiento a celdas enteras
  const g = ${JSON.stringify(process.env.ANCLA || '')} && svg.querySelector('[id="' + ${JSON.stringify(process.env.ANCLA || '')} + '"]');
  const ancla = g ? (m => [m.e, m.f])(inv.multiply(g.getScreenCTM())) : null;
  return JSON.stringify({ piezas: out, ancla });
};
window.VB = vb; window.DUR = gsap.globalTimeline.getChildren(false).map(c => [c.duration(), c.totalDuration(), c.delay()]);
</script></body></html>`;

(async () => {
  const nav = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true,
  });
  const p = await nav.newPage();
  p.on('pageerror', e => console.error('ERROR PAGINA', e.message));
  await p.setContent(html, { waitUntil: 'load' });
  const vb = await p.evaluate(() => window.VB); console.log('lineas', JSON.stringify(await p.evaluate(() => window.DUR)));
  // dt puede ser un paso fijo ("0.04") o una lista de instantes ("[0.001,0.086]")
  const instantes = dt.startsWith('[') ? JSON.parse(dt)
    : Array.from({ length: Math.round(Number(dur) / Number(dt)) + 1 }, (_, k) => k * Number(dt));
  const pasos = instantes.length - 1;
  // GEOMETRIA=1 guarda poligonos (.json) en vez de SVG: es lo que usa la
  // transcripcion por piezas de animaciones con rotaciones (paseo)
  const geo = process.env.GEOMETRIA === '1';
  for (let k = 0; k <= pasos; k++) {
    const s = await p.evaluate((x, g) => (g ? window.poligonos(x) : window.ir(x)), instantes[k], geo);
    fs.writeFileSync(path.join(salida, `t${String(k).padStart(4, '0')}.${geo ? 'json' : 'svg'}`), s);
  }
  fs.writeFileSync(path.join(salida, 'meta.json'), JSON.stringify({ vb, instantes, pasos }));
  console.log('ok', pasos + 1, 'instantes, viewBox', vb.join(' '));
  await nav.close();
})();
