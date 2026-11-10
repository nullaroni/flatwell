// nice!nano v2: Pro Micro form factor plus three extra pins (P1.01, P1.02,
// P1.07). Pad positions from github.com/bstiq/nice-nano-kicad (nice_nano.kicad_mod),
// drawn as a top view with the nice!nano's components facing away from the PCB.
//
// side: 'F' mounts it on top. 'B' mounts it underneath, still components-out
// (facing down), which mirrors the pin pattern. Confirm against a real nice!nano
// on a 1:1 printout before ordering.
//
// USB end is at -x. Net params are named after the nRF52840 GPIO on each pad;
// GND/VCC/RST/BAT are fixed. Unused pads keep their own single-pad nets.

const pads = [
  // [pad, x, y, param]
  [1, -13.97, 7.62, 'P0_06'], [2, -11.43, 7.62, 'P0_08'], [3, -8.89, 7.62, 'GND'], [4, -6.35, 7.62, 'GND'],
  [5, -3.81, 7.62, 'P0_17'], [6, -1.27, 7.62, 'P0_20'], [7, 1.27, 7.62, 'P0_22'], [8, 3.81, 7.62, 'P0_24'],
  [9, 6.35, 7.62, 'P1_00'], [10, 8.89, 7.62, 'P0_11'], [11, 11.43, 7.62, 'P1_04'], [12, 13.97, 7.62, 'P1_06'],
  [13, 13.97, -7.62, 'P0_09'], [14, 11.43, -7.62, 'P0_10'], [15, 8.89, -7.62, 'P1_11'], [16, 6.35, -7.62, 'P1_13'],
  [17, 3.81, -7.62, 'P1_15'], [18, 1.27, -7.62, 'P0_02'], [19, -1.27, -7.62, 'P0_29'], [20, -3.81, -7.62, 'P0_31'],
  [21, -6.35, -7.62, 'VCC'], [22, -8.89, -7.62, 'RST'], [23, -11.43, -7.62, 'GND'], [24, -13.97, -7.62, 'BAT'],
  [31, 8.89, 5.08, 'P1_01'], [32, 8.89, 2.54, 'P1_02'], [33, 8.89, 0, 'P1_07'],
]

const params = { designator: 'MCU', side: 'F' }
for (const [, , , name] of pads) params[name] = { type: 'net', value: name }

module.exports = {
  params,
  body: p => {
    const back = p.side === 'B'
    const S = back ? 'B' : 'F'
    const m = back ? -1 : 1 // mirror y for the back
    const mirror = back ? ' (justify mirror)' : ''
    const line = (x1, y1, x2, y2) => `(fp_line (start ${x1} ${m * y1}) (end ${x2} ${m * y2}) (layer ${S}.SilkS) (width 0.15))`
    return `
    (module nice_nano (layer ${S}.Cu) (tedit 0)
      ${p.at /* parametric position */}
      (fp_text reference "${p.ref}" (at 0 0 ${p.r}) (layer ${S}.SilkS) ${p.ref_hide} (effects (font (size 1.27 1.27) (thickness 0.15))${mirror}))
      (fp_text value "nice!nano" (at 0 0 ${p.r}) (layer ${S}.Fab) hide (effects (font (size 1.27 1.27) (thickness 0.15))${mirror}))
      ${line(-17.78, -8.89, 15.24, -8.89)}
      ${line(15.24, -8.89, 15.24, 8.89)}
      ${line(15.24, 8.89, -17.78, 8.89)}
      ${line(-17.78, 8.89, -17.78, -8.89)}
      (fp_text user "USB" (at -16 0 ${p.r + 90}) (layer ${S}.SilkS) (effects (font (size 1 1) (thickness 0.15))${mirror}))
      ${pads.map(([n, x, y, name]) => `(pad ${n} thru_hole ${n === 1 ? 'rect' : 'circle'} (at ${x} ${m * y} ${p.r}) (size 1.7526 1.7526) (drill 1.0922) (layers *.Cu *.Mask) ${p[name]})`).join('\n      ')}
    )
  `
  },
}
