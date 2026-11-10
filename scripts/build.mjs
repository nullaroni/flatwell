#!/usr/bin/env node
// Builds every layout variant in ergogen/variants.yaml:
//   output/<variant>/outlines/*.{dxf,svg}  fab outlines from Ergogen
//   output/<variant>/points.json           key positions + matrix nets
//   output/<variant>/flatwell.kicad_pcb    unrouted key PCB (open in KiCad to route)
//   preview/index.html                     labeled previews of all variants
//   preview/print.html                     1:1 print sheets, one half per Letter page (portrait)
// The trackpad goes one rim below the lowest key above it. Each variant is checked:
// every key has a legend and its own matrix position; on the PCB every key is a
// switch + diode pair and every row/column reaches the nice!nano; no keycap
// touches another key or the trackpad pocket rim; and the case stays
// inside the size limit (bag_w x bag_h, a 16-inch MacBook Pro).
import { createRequire } from 'node:module'
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const require = createRequire(import.meta.url)
const ergogen = require('ergogen')
const yaml = require('js-yaml')
const { LEGENDS, TRACKPAD } = await import('./legends.mjs')

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
for (const fp of ['nicenano', 'sod123']) {
  ergogen.inject('footprint', fp, require(join(root, `ergogen/footprints/${fp}.js`)))
}
const base = yaml.load(readFileSync(join(root, 'ergogen/config.yaml'), 'utf8'))
const variants = yaml.load(readFileSync(join(root, 'ergogen/variants.yaml'), 'utf8'))

const rendered = []
let failed = false

for (const [id, variant] of Object.entries(variants)) {
  const config = structuredClone(base)
  Object.assign(config.units, variant.units)
  // Draft pass to find how high the trackpad can sit, then the real build.
  config.units.tp_cy = trackpadY(await ergogen.process(config, { debug: true }))
  const res = await ergogen.process(config, { debug: true, svg: true })

  const outDir = join(root, 'output', id)
  mkdirSync(join(outDir, 'outlines'), { recursive: true })
  for (const [name, o] of Object.entries(res.outlines)) {
    writeFileSync(join(outDir, 'outlines', `${name}.dxf`), o.dxf)
    writeFileSync(join(outDir, 'outlines', `${name}.svg`), o.svg)
  }
  const pcb = res.pcbs.flatwell
  writeFileSync(join(outDir, 'flatwell.kicad_pcb'), pcb)

  const keys = toKeys(res.points)
  writeFileSync(join(outDir, 'points.json'), JSON.stringify(keys, null, 2))

  const u = res.units
  const tp = {
    cx: u.tp_cx, cy: u.tp_cy,
    w: u.tp_w + 2 * u.tp_clear, h: u.tp_d + 2 * u.tp_clear,
  }

  const box = caseBox(keys, tp, u.wall)
  const problems = [...checkMatrix(keys), ...checkPcb(pcb, keys), ...checkClearance(keys, tp, u.rim)]
  if (box.w > u.bag_w || box.h > u.bag_h) {
    problems.push(`case is ${f(box.w)} × ${f(box.h)} mm; the size limit is ${u.bag_w} × ${u.bag_h} mm`)
  }
  if (problems.length) {
    failed = true
    console.error(`✗ ${id}:\n  ${problems.join('\n  ')}`)
  } else {
    const rows = new Set(keys.map(k => k.row)).size, cols = new Set(keys.map(k => k.col)).size
    console.log(`✓ ${id}: ${keys.length} keys on a ${rows} × ${cols} matrix (${rows + cols} nice!nano pins), ` +
      `PCB nets OK, no collisions, case ${f(box.w)} × ${f(box.h)} mm fits the ${u.bag_w} × ${u.bag_h} mm limit`)
  }

  // Rough resting spot of the palm heel: ~92 mm below the middle finger on home row
  const mid = res.points.matrix_middle_home
  const palms = [-1, 1].map(s => ({ cx: s * (Math.abs(mid.x) - 8), cy: mid.y - 92 }))
  rendered.push({ id, ...variant, keys, tp, palms, box, u })
}

writeFileSync(join(root, 'preview/index.html'), page(rendered))
writeFileSync(join(root, 'preview/print.html'), printPage(rendered))
console.log('→ preview/index.html, preview/print.html')
if (failed) process.exit(1)

// --- checks ---------------------------------------------------------------

function toKeys(points) {
  return Object.values(points).map(p => ({
    name: p.meta.name,
    x: p.x, y: p.y, r: p.r,
    w: p.meta.width, h: p.meta.height,
    row: p.meta.row_net, col: p.meta.col_net,
  }))
}

// Trackpad pocket center: its rim touches the lowest keycap that sits over it.
function trackpadY(res) {
  const u = res.units
  const half = u.tp_w / 2 + u.tp_clear + u.rim
  const over = toKeys(res.points).flatMap(corners).filter(([x]) => Math.abs(x) < half)
  return Math.min(...over.map(([, y]) => y)) - u.rim - u.tp_clear - u.tp_d / 2
}

function label(k) { return `${LEGENDS[k.name] ?? '?'} (${k.name})` }

function checkMatrix(keys) {
  const problems = []
  const seen = new Map()
  for (const k of keys) {
    if (!LEGENDS[k.name]) problems.push(`${k.name} has no legend in scripts/legends.mjs`)
    if (!k.row || !k.col) { problems.push(`${label(k)} has no matrix position`); continue }
    const rc = `${k.row}/${k.col}`
    if (seen.has(rc)) problems.push(`${label(k)} and ${label(seen.get(rc))} are both on ${rc}`)
    seen.set(rc, k)
  }
  const names = new Set(keys.map(k => k.name))
  for (const n of Object.keys(LEGENDS)) if (!names.has(n)) problems.push(`legend for ${n}, but there's no such key`)
  return problems
}

// On the PCB: each key's own net joins exactly one switch and one diode, and
// every row and column net reaches a nice!nano pin.
function checkPcb(text, keys) {
  const problems = []
  const modules = text.split(/\(module /).slice(1).map(chunk => ({
    type: chunk.slice(0, chunk.search(/\s/)),
    nets: new Set([...chunk.matchAll(/\(net \d+ "([^"]*)"\)/g)].map(m => m[1])),
  }))
  for (const k of keys) {
    const on = modules.filter(m => m.nets.has(k.name)).map(m => m.type).sort().join(' + ')
    if (on !== 'D_SOD-123 + PG1350') problems.push(`${label(k)}: its switch-diode net joins ${on || 'nothing'}`)
  }
  const mcu = modules.find(m => m.type === 'nice_nano')
  if (!mcu) return [...problems, 'no nice!nano on the PCB']
  for (const net of new Set(keys.flatMap(k => [k.row, k.col]))) {
    if (!mcu.nets.has(net)) problems.push(`${net} isn't wired to a nice!nano pin`)
  }
  return problems
}

// Keycaps must not touch each other or the trackpad pocket plus its rim.
function checkClearance(keys, tp, rim) {
  const problems = []
  const caps = keys.map(k => [k, corners(k)])
  const pocket = rect(tp.cx, tp.cy, tp.w + 2 * rim, tp.h + 2 * rim)
  for (let i = 0; i < caps.length; i++) {
    const [k, a] = caps[i]
    if (overlaps(a, pocket)) problems.push(`${label(k)} is within ${rim} mm of the trackpad pocket`)
    for (let j = i + 1; j < caps.length; j++) {
      if (overlaps(a, caps[j][1])) problems.push(`${label(k)} overlaps ${label(caps[j][0])}`)
    }
  }
  return problems
}

// Separating-axis test for two convex polygons.
function overlaps(A, B) {
  for (const P of [A, B]) {
    for (let i = 0; i < P.length; i++) {
      const [x1, y1] = P[i], [x2, y2] = P[(i + 1) % P.length]
      const nx = y2 - y1, ny = x1 - x2
      const a = A.map(([x, y]) => x * nx + y * ny), b = B.map(([x, y]) => x * nx + y * ny)
      if (Math.max(...a) <= Math.min(...b) + 1e-6 || Math.max(...b) <= Math.min(...a) + 1e-6) return false
    }
  }
  return true
}

// --- preview --------------------------------------------------------------

function corners(k) {
  const a = (k.r * Math.PI) / 180, c = Math.cos(a), s = Math.sin(a)
  return [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sy]) => {
    const dx = (sx * k.w) / 2, dy = (sy * k.h) / 2
    return [k.x + dx * c - dy * s, k.y + dx * s + dy * c]
  })
}

// Case outline: a rounded rectangle around every keycap and the trackpad
// pocket, plus `wall` on each side.
function caseBox(keys, tp, wall) {
  const pts = keys.flatMap(corners)
    .concat(rect(tp.cx, tp.cy, tp.w, tp.h))
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1])
  const x0 = Math.min(...xs) - wall, x1 = Math.max(...xs) + wall
  const y0 = Math.min(...ys) - wall, y1 = Math.max(...ys) + wall
  return { x0, x1, y0, y1, w: x1 - x0, h: y1 - y0 }
}

function rect(cx, cy, w, h) {
  return [[cx - w / 2, cy - h / 2], [cx + w / 2, cy - h / 2], [cx + w / 2, cy + h / 2], [cx - w / 2, cy + h / 2]]
}
function f(n) { return +n.toFixed(2) }

// opts.half: 'left' | 'right' crops to one half (plus 10 mm past the center
// line) and sizes the SVG in real millimetres, for 1:1 printing.
function svg(v, opts = {}) {
  const { box } = v
  const showPalms = !opts.half
  const pad = opts.half ? 2 : 8
  let minX = box.x0 - pad, maxX = box.x1 + pad
  let minY = box.y0 - pad, maxY = box.y1 + pad
  if (showPalms) for (const p of v.palms) minY = Math.min(minY, p.cy - 24 - pad)
  if (!opts.half) {
    const slack = Math.max(0, (v.u.bag_h - box.h) / 2)
    minX = Math.min(minX, -v.u.bag_w / 2 - pad); maxX = Math.max(maxX, v.u.bag_w / 2 + pad)
    minY = Math.min(minY, box.y0 - slack - pad); maxY = Math.max(maxY, box.y1 + slack + pad)
  }
  if (opts.half === 'left') maxX = 10
  if (opts.half === 'right') minX = -10
  const W = maxX - minX, H = maxY - minY
  const size = opts.half ? `width="${f(W)}mm" height="${f(H)}mm"` : ''
  const bar = opts.half ? scaleBar(opts.half === 'left' ? minX + 6 : maxX - 56, -minY - 5) : ''
  const centerLine = opts.half ? `<line class="center" x1="0" y1="${f(-maxY)}" x2="0" y2="${f(-minY)}"/>
    <text class="center-label" x="${opts.half === 'left' ? -2 : 2}" y="${f(-minY - 3)}" text-anchor="${opts.half === 'left' ? 'end' : 'start'}">center line: overlap and tape here</text>` : ''

  const keySvg = v.keys.map(k => {
    const legend = LEGENDS[k.name] ?? '?'
    const small = legend.length > 3
    return `<g transform="translate(${f(k.x)} ${f(-k.y)}) rotate(${f(-k.r)})">
      <rect class="cap" x="${f(-k.w / 2)}" y="${f(-k.h / 2)}" width="${f(k.w)}" height="${f(k.h)}" rx="2"/>
      <text class="legend${small ? ' sm' : ''}" y="${small ? 1.1 : 1.6}">${esc(legend)}</text>
      <title>${esc(legend)} · ${k.name} · ${k.row} / ${k.col}</title></g>`
  }).join('\n')

  return `<svg class="board" viewBox="${f(minX)} ${f(-maxY)} ${f(W)} ${f(H)}" data-w="${f(W)}" data-h="${f(H)}" data-case-w="${f(box.w)}" data-case-h="${f(box.h)}" ${size}
    role="img" aria-label="${esc(v.title)} layout, ${Math.round(W)} by ${Math.round(H)} mm">
    <rect class="case" x="${f(box.x0)}" y="${f(-box.y1)}" width="${f(box.w)}" height="${f(box.h)}" rx="12"/>
    ${opts.half ? '' : `<rect class="bag" x="${f(-v.u.bag_w / 2)}" y="${f(-(box.y1 + (v.u.bag_h - box.h) / 2))}" width="${v.u.bag_w}" height="${v.u.bag_h}" rx="12"><title>Size limit: ${v.u.bag_w} × ${v.u.bag_h} mm</title></rect>`}
    <rect class="tp" x="${f(v.tp.cx - v.tp.w / 2)}" y="${f(-(v.tp.cy + v.tp.h / 2))}" width="${f(v.tp.w)}" height="${f(v.tp.h)}" rx="8"/>
    <text class="tp-label" x="${f(v.tp.cx)}" y="${f(-v.tp.cy)}">Magic Trackpad</text>
    <text class="tp-sub" x="${f(v.tp.cx)}" y="${f(-v.tp.cy + 6)}">${TRACKPAD.w} × ${TRACKPAD.d} mm</text>
    ${keySvg}
    ${showPalms ? v.palms.map(p => `<ellipse class="palm" cx="${f(p.cx)}" cy="${f(-p.cy)}" rx="38" ry="24"/>
    <text class="palm-label" x="${f(p.cx)}" y="${f(-p.cy + 1.4)}">palm (approx.)</text>`).join('') : ''}
    ${centerLine}
    ${bar}
  </svg>`
}

// 50 mm ruler: measure it after printing to confirm the scale is 1:1.
function scaleBar(x, y) {
  const ticks = [0, 10, 20, 30, 40, 50].map(t =>
    `<line x1="${f(x + t)}" y1="${f(y - (t % 50 ? 1.5 : 3))}" x2="${f(x + t)}" y2="${f(y)}"/>`).join('')
  return `<g class="scale"><line x1="${f(x)}" y1="${f(y)}" x2="${f(x + 50)}" y2="${f(y)}"/>${ticks}
    <text x="${f(x + 25)}" y="${f(y - 4)}">50 mm: measure to check 100% scale</text></g>`
}

function printPage(vs) {
  const pages = vs.flatMap(v => ['left', 'right'].map(half => {
    const s = svg(v, { half })
    const w = +s.match(/data-w="([\d.]+)"/)[1], h = +s.match(/data-h="([\d.]+)"/)[1]
    if (w > 203 || h > 266) console.warn(`! ${v.id} ${half} half is ${Math.round(w)} × ${Math.round(h)} mm; may not fit Letter portrait`)
    return `<section class="sheet"><div class="cap-line">${esc(v.title)} · ${half} half · print at 100% (no "fit to page")</div>${s}</section>`
  })).join('\n')
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Flatwell print sheets</title>
<style>
  @page { size: letter portrait; margin: 6mm }
  body { margin:0; background:#fff; color:#111; font:11px -apple-system, system-ui, sans-serif }
  .sheet { break-after:page; padding:0 } .sheet:last-child { break-after:auto }
  .cap-line { font-size:9pt; color:#555; margin:0 0 1mm }
  svg { display:block; overflow:hidden }
  .case { fill:#f1f0ec; stroke:#999; stroke-width:.3 }
  .cap { fill:#fff; stroke:#333; stroke-width:.3 }
  .legend { font-size:4.2px; text-anchor:middle; fill:#111 } .legend.sm { font-size:3px }
  .tp { fill:#eef2f7; stroke:#333; stroke-width:.4; stroke-dasharray:3 2 }
  .tp-label { font-size:6px; text-anchor:middle; fill:#111 } .tp-sub { font-size:4px; text-anchor:middle; fill:#555 }
  .center { stroke:#c00; stroke-width:.3; stroke-dasharray:2 1.5 } .center-label { font-size:3.2px; fill:#c00 }
  .scale line { stroke:#111; stroke-width:.3 } .scale text { font-size:3px; text-anchor:middle; fill:#111 }
  @media screen { body { padding:16px } .sheet { margin-bottom:24px } }
</style></head>
<body>
${pages}
</body></html>`
}

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function page(vs) {
  const sections = vs.map(v => {
    const s = svg(v)
    const w = s.match(/data-case-w="([\d.]+)"/)[1], h = s.match(/data-case-h="([\d.]+)"/)[1]
    return `<section>
      <header><h2>${esc(v.title)}</h2><span class="dims">${Math.round(w)} × ${Math.round(h)} mm case · variant <code>${v.id}</code></span></header>
      <p>${esc(v.note.trim())}</p>
      <div class="frame">${s}</div>
    </section>`
  }).join('\n')

  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Flatwell layouts</title>
<style>
  :root { --bg:#f6f5f2; --fg:#1d1d1f; --muted:#6e6e73; --case:#e3e1dc; --cap:#fff; --cap-stroke:#b9b6ae;
          --tp:#d7dde6; --tp-stroke:#8c97a8; --accent:#0a66d8; }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
          --bg:#151517; --fg:#ececee; --muted:#9a9aa0; --case:#2a2a2e; --cap:#3a3a3f; --cap-stroke:#55555c;
          --tp:#33404f; --tp-stroke:#6f8199; --accent:#5aa2ff; } }
  :root[data-theme="dark"] { --bg:#151517; --fg:#ececee; --muted:#9a9aa0; --case:#2a2a2e; --cap:#3a3a3f; --cap-stroke:#55555c;
          --tp:#33404f; --tp-stroke:#6f8199; --accent:#5aa2ff; }
  * { box-sizing:border-box }
  body { margin:0; padding:24px 16px 48px; background:var(--bg); color:var(--fg);
         font:15px/1.5 -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif; }
  main { max-width:1100px; margin:0 auto }
  h1 { font-size:22px; margin:0 0 4px } h2 { font-size:17px; margin:0 }
  .lede { color:var(--muted); margin:0 0 24px; max-width:70ch }
  section { margin:0 0 36px }
  header { display:flex; flex-wrap:wrap; gap:4px 12px; align-items:baseline }
  .dims { color:var(--muted); font-size:13px }
  section p { margin:6px 0 12px; max-width:75ch; color:var(--muted) }
  .frame { overflow:hidden }
  svg.board { width:100%; height:auto; display:block }
  .case { fill:var(--case) }
  .bag { fill:none; stroke:var(--accent); stroke-width:.5; stroke-dasharray:3 2 }
  .cap { fill:var(--cap); stroke:var(--cap-stroke); stroke-width:.4 }
  .legend { font-size:4.2px; text-anchor:middle; fill:var(--fg); font-weight:500 }
  .legend.sm { font-size:3px }
  .tp { fill:var(--tp); stroke:var(--tp-stroke); stroke-width:.5 }
  .tp-label { font-size:6px; text-anchor:middle; fill:var(--fg); font-weight:600 }
  .tp-sub { font-size:4px; text-anchor:middle; fill:var(--muted) }
  .palm { fill:none; stroke:var(--muted); stroke-width:.6; stroke-dasharray:2 1.6 }
  .palm-label { font-size:4px; text-anchor:middle; fill:var(--muted) }
  code { font:12px ui-monospace, Menlo, monospace }
</style></head>
<body><main>
  <h1>Flatwell layout variants</h1>
  <p class="lede">Generated by <code>npm run build</code> from <code>ergogen/config.yaml</code>. Hover a key for its
  matrix row and column. Gray shape: case outline. Dashed blue: the size limit (a 16-inch MacBook Pro's footprint). Dashed ovals: roughly where your palms rest.
  For a 1:1 paper test, print <code>print.html</code>.</p>
  ${sections}
</main></body></html>`
}
