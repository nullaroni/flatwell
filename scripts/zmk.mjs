#!/usr/bin/env node
// Generates the ZMK shield in firmware/ from the same sources as the PCB, so
// the firmware can't drift from the board:
//   pins    <- ergogen/config.yaml (pcbs.flatwell.footprints.mcu.params)
//   matrix  <- output/<variant>/points.json (each key's row/col net and position)
//   keymap  <- scripts/legends.mjs (base layer) + the Fn layer below
// Run `npm run build` first. `npm run firmware` runs this, then builds the .uf2.
import { createRequire } from 'node:module'
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const require = createRequire(import.meta.url)
const yaml = require('js-yaml')
const { LEGENDS } = await import('./legends.mjs')

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const variant = process.argv[2] ?? 'macbook'
const config = yaml.load(readFileSync(join(root, 'ergogen/config.yaml'), 'utf8'))
const keys = JSON.parse(readFileSync(join(root, 'output', variant, 'points.json'), 'utf8'))
const byName = Object.fromEntries(keys.map(k => [k.name, k]))

// --- pins -------------------------------------------------------------------

const pinOf = {} // net -> "&gpio0 6"
for (const [param, net] of Object.entries(config.pcbs.flatwell.footprints.mcu.params)) {
  const m = /^P(\d)_(\d\d)$/.exec(param)
  if (m) pinOf[net] = `&gpio${m[1]} ${+m[2]}`
}
const nets = prefix => [...new Set(keys.map(k => k[prefix === 'R' ? 'row' : 'col']))]
  .sort((a, b) => +a.slice(1) - +b.slice(1))
const rows = nets('R'), cols = nets('C')
for (const n of [...rows, ...cols]) if (!pinOf[n]) throw new Error(`${n} has no nice!nano pin`)

// --- key order (how the keymap reads, left to right, top to bottom) ---------

const COLS = ['outer', 'pinky', 'ring', 'middle', 'index', 'inner']
const order = []
for (const row of ['num', 'top', 'home', 'zrow', 'bottom']) {
  const line = [
    ...COLS.map(c => `matrix_${c}_${row}`),
    ...[...COLS].reverse().map(c => `mirror_matrix_${c}_${row}`),
  ].filter(n => byName[n])
  order.push(line)
}
order.push([
  'thumb_bspc_low', 'thumb_del_low', 'thumb_nav_high', 'thumb_nav_low',
  'mirror_thumb_nav_low', 'mirror_thumb_nav_high', 'mirror_thumb_del_low', 'mirror_thumb_bspc_low',
])
const flat = order.flat()
if (flat.length !== keys.length || new Set(flat).size !== keys.length || flat.some(n => !byName[n])) {
  throw new Error('key order does not cover every key exactly once')
}

// --- keymap -----------------------------------------------------------------

const CODES = {
  '=': 'EQUAL', '-': 'MINUS', '\\': 'BSLH', "'": 'SQT', ';': 'SEMI', '/': 'FSLH', '.': 'DOT', ',': 'COMMA',
  '`': 'GRAVE', '[': 'LBKT', ']': 'RBKT', '←': 'LEFT', '→': 'RIGHT', '↑': 'UP', '↓': 'DOWN',
  Tab: 'TAB', Esc: 'ESC', Bksp: 'BSPC', Del: 'DEL', End: 'END', PgDn: 'PG_DN', Enter: 'RET', Space: 'SPACE',
}
function base(name) {
  const l = LEGENDS[name]
  if (l === 'Fn') return '&mo FN'
  if (l === 'Shift') return name.startsWith('mirror_') ? '&kp RSHFT' : '&kp LSHFT'
  if (l === 'Ctrl') return name.startsWith('mirror_') ? '&kp RCTRL' : '&kp LCTRL'
  if (/^[A-Z]$/.test(l)) return `&kp ${l}`
  if (/^[0-9]$/.test(l)) return `&kp N${l}`
  if (CODES[l]) return `&kp ${CODES[l]}`
  throw new Error(`no ZMK keycode for legend "${l}" (${name})`)
}

// Fn layer, by base-layer legend of the key it sits on. Everything the
// Advantage2 had that this board has no key for, plus Bluetooth and flashing.
const FN = {
  '=': '&kp F11', 1: '&kp F1', 2: '&kp F2', 3: '&kp F3', 4: '&kp F4', 5: '&kp F5',
  6: '&kp F6', 7: '&kp F7', 8: '&kp F8', 9: '&kp F9', 0: '&kp F10', '-': '&kp F12',
  Q: '&bt BT_SEL 0', W: '&bt BT_SEL 1', E: '&bt BT_SEL 2', R: '&bt BT_SEL 3', T: '&bt BT_CLR',
  Y: '&out OUT_TOG', P: '&kp PSCRN', '\\': '&bootloader', Tab: '&studio_unlock',
  '←': '&kp HOME', '→': '&kp END', '↑': '&kp PG_UP', '↓': '&kp PG_DN',
  'Ctrl:left': '&kp LALT', 'Ctrl:right': '&kp RGUI',
  Bksp: '&kp LGUI', Space: '&kp RALT',
}
function fn(name) {
  const l = LEGENDS[name]
  return FN[`${l}:${name.startsWith('mirror_') ? 'right' : 'left'}`] ?? FN[l] ?? '&trans'
}

function layer(binding) {
  return order.map(line => {
    const cells = line.map(binding)
    const w = Math.max(...flat.map(n => binding(n).length))
    return '        ' + cells.map(c => c.padEnd(w)).join(' ').trimEnd()
  }).join('\n')
}

// --- physical layout (ZMK Studio draws the board from this) -----------------

const U = 18 // mm per key unit
const minX = Math.min(...keys.map(k => k.x - k.w / 2 - 10)), maxY = Math.max(...keys.map(k => k.y + k.h / 2 + 10))
const c = mm => Math.round((mm / U) * 100)
const attrs = flat.map(n => {
  const k = byName[n]
  const cx = k.x - minX, cy = maxY - k.y
  const cell = [c(k.w + 1), c(k.h + 1), c(cx - (k.w + 1) / 2), c(cy - (k.h + 1) / 2), Math.round(-k.r * 100), c(cx), c(cy)]
  const s = cell.map((v, i) => (v < 0 ? `(${v})` : `${v}`).padStart(i < 2 ? 4 : 7)).join(' ')
  return `<&key_physical_attrs ${s}>  // ${LEGENDS[n]}`
})

// --- files ------------------------------------------------------------------

const nfcPins = [...rows, ...cols].filter(n => ['&gpio0 9', '&gpio0 10'].includes(pinOf[n]))
const rc = n => `RC(${rows.indexOf(byName[n].row)},${cols.indexOf(byName[n].col)})`
const HEADER = '// Generated by scripts/zmk.mjs. Edit that (or ergogen/config.yaml), not this file.\n'
const gpios = (list, flags) => list.map(n => `<${pinOf[n]} ${flags}>`).join('\n            , ')

const files = {
  'zephyr/module.yml': `build:\n  settings:\n    board_root: .\n`,
  'boards/shields/flatwell/Kconfig.shield':
    `config SHIELD_FLATWELL\n    def_bool $(shields_list_contains,flatwell)\n`,
  'boards/shields/flatwell/Kconfig.defconfig':
    `if SHIELD_FLATWELL\n\nconfig ZMK_KEYBOARD_NAME\n    default "Flatwell"\n\nendif\n`,
  'boards/shields/flatwell/flatwell.zmk.yml': `file_format: "1"
id: flatwell
name: Flatwell
type: shield
url: https://github.com/nullaroni/flatwell
requires: [pro_micro]
features:
  - keys
  - studio
`,
  'boards/shields/flatwell/flatwell.conf': `# Deep sleep after 15 min idle; any key wakes it.
CONFIG_ZMK_SLEEP=y
# Stronger radio for a keyboard that shares a case with two other Bluetooth devices.
CONFIG_BT_CTLR_TX_PWR_PLUS_8=y
`,
  'boards/shields/flatwell/flatwell-layouts.dtsi': `${HEADER}
#include <physical_layouts.dtsi>

/ {
    physical_layout0: physical_layout_0 {
        compatible = "zmk,physical-layout";
        display-name = "Flatwell";
        transform = <&default_transform>;
        kscan = <&kscan0>;

        keys  //                     w    h       x       y     rot      rx      ry
            = ${attrs.join('\n            , ')}
            ;
    };
};
`,
  'boards/shields/flatwell/flatwell.overlay': `${HEADER}
#include <dt-bindings/zmk/matrix_transform.h>
#include "flatwell-layouts.dtsi"

${nfcPins.length ? `// ${nfcPins.join(' and ')} use${nfcPins.length > 1 ? '' : 's'} an NFC antenna pin (P0.09/P0.10) as a plain GPIO.
&uicr {
    nfct-pins-as-gpios;
};

` : ''}/ {
    chosen {
        zmk,physical-layout = &physical_layout0;
    };

    // ${rows.length} rows x ${cols.length} columns, col2row: column -> switch -> diode -> row.
    // Rows ${rows[0]}-${rows[rows.length / 2 - 1]} are the left half, ${rows[rows.length / 2]}-${rows[rows.length - 1]} the right.
    kscan0: kscan0 {
        compatible = "zmk,kscan-gpio-matrix";
        diode-direction = "col2row";
        wakeup-source;

        row-gpios  // ${rows.join(' ')}
            = ${gpios(rows, '(GPIO_ACTIVE_HIGH | GPIO_PULL_DOWN)')}
            ;
        col-gpios  // ${cols.join(' ')}
            = ${gpios(cols, 'GPIO_ACTIVE_HIGH')}
            ;
    };

    default_transform: keymap_transform0 {
        compatible = "zmk,matrix-transform";
        rows = <${rows.length}>;
        columns = <${cols.length}>;
        map = <
${order.map(line => '            ' + line.map(rc).join(' ')).join('\n')}
        >;
    };
};
`,
  'config/flatwell.keymap': `${HEADER}
#include <behaviors.dtsi>
#include <dt-bindings/zmk/keys.h>
#include <dt-bindings/zmk/bt.h>
#include <dt-bindings/zmk/outputs.h>

#define BASE 0
#define FN 1

/ {
    keymap {
        compatible = "zmk,keymap";

        base {
            display-name = "Base";
            bindings = <
${layer(base)}
            >;
        };

        fn {
            display-name = "Fn";
            bindings = <
${layer(fn)}
            >;
        };

        extra1 { status = "reserved"; };
        extra2 { status = "reserved"; };
    };
};
`,
  'config/flatwell.conf': `# User settings; shield defaults are in boards/shields/flatwell/flatwell.conf.
CONFIG_ZMK_STUDIO=y
`,
  'config/west.yml': `manifest:
  remotes:
    - name: zmkfirmware
      url-base: https://github.com/zmkfirmware
  projects:
    - name: zmk
      remote: zmkfirmware
      revision: main
      import: app/west.yml
  self:
    path: config
`,
  'build.yaml': `# For ZMK's GitHub Actions build, if this folder is pushed as a zmk-config repo.
include:
  - board: nice_nano//zmk
    shield: flatwell
    snippet: studio-rpc-usb-uart
`,
}

for (const [path, text] of Object.entries(files)) {
  const full = join(root, 'firmware', path)
  mkdirSync(dirname(full), { recursive: true })
  writeFileSync(full, text)
}
console.log(`✓ firmware/: ${keys.length} keys, ${rows.length} rows (${rows.map(r => pinOf[r].replace('&gpio', 'P').replace(' ', '.')).join(' ')}), ` +
  `${cols.length} columns (${cols.map(r => pinOf[r].replace('&gpio', 'P').replace(' ', '.')).join(' ')})`)
