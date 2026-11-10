// Key legends by Ergogen point name, for previews (and later the default keymap).
// Advantage2 base layer, minus the function row and the Alt/Home/Cmd/PgUp thumb keys,
// with Esc where Caps Lock was (no Caps Lock anywhere).

const COLS = ['outer', 'pinky', 'ring', 'middle', 'index', 'inner']
const LEFT = {
  num: ['=', '1', '2', '3', '4', '5'],
  top: ['Tab', 'Q', 'W', 'E', 'R', 'T'],
  home: ['Esc', 'A', 'S', 'D', 'F', 'G'],   // Esc replaces Caps Lock
  zrow: ['Shift', 'Z', 'X', 'C', 'V', 'B'],
  bottom: [null, '`', 'Fn', '←', '→', null],   // Fn replaces Insert
}
// Right half, listed outer -> inner like the left (it's mirrored)
const RIGHT = {
  num: ['-', '0', '9', '8', '7', '6'],
  top: ['\\', 'P', 'O', 'I', 'U', 'Y'],
  home: ["'", ';', 'L', 'K', 'J', 'H'],
  zrow: ['Shift', '/', '.', ',', 'M', 'N'],
  bottom: [null, ']', '[', '↓', '↑', null],
}

export const LEGENDS = {}
for (const [rows, prefix] of [[LEFT, ''], [RIGHT, 'mirror_']]) {
  for (const [row, legends] of Object.entries(rows)) {
    legends.forEach((l, i) => { if (l) LEGENDS[`${prefix}matrix_${COLS[i]}_${row}`] = l })
  }
}
Object.assign(LEGENDS, {
  thumb_bspc_low: 'Bksp', thumb_del_low: 'Del', thumb_nav_high: 'Ctrl', thumb_nav_low: 'End',
  mirror_thumb_bspc_low: 'Space', mirror_thumb_del_low: 'Enter', mirror_thumb_nav_high: 'Ctrl', mirror_thumb_nav_low: 'PgDn',
})

// Apple spec, Magic Trackpad (USB-C): 160 x 114.9 mm, 4.9-10.9 mm tall
export const TRACKPAD = { w: 160, d: 114.9 }
