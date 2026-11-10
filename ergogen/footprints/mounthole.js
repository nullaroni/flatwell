// Unplated M3 mounting hole (3.4 mm). The pad is drawn 5.8 mm wide, with no copper, so
// the autorouter keeps traces 1.2 mm away from the hole.
// A case screw passes through it into a threaded insert in the tray post below.

module.exports = {
  params: { designator: 'H' },
  body: p => `
    (module MountingHole_M3 (layer F.Cu) (tedit 0)
      ${p.at /* parametric position */}
      (fp_text reference "${p.ref}" (at 0 0) (layer F.Fab) hide (effects (font (size 1 1) (thickness 0.15))))
      (fp_text value "M3" (at 0 0) (layer F.Fab) hide (effects (font (size 1 1) (thickness 0.15))))
      (fp_circle (center 0 0) (end 3.5 0) (layer F.Fab) (width 0.1))
      (fp_circle (center 0 0) (end 3.5 0) (layer B.Fab) (width 0.1))
      (pad "" np_thru_hole circle (at 0 0) (size 5.8 5.8) (drill 3.4) (layers *.Cu *.Mask))
    )
  `,
}
