// SOD-123 diode (e.g. 1N4148W) on the back of the board, for machine assembly.
// Pad 1 is the cathode (`to`), pad 2 the anode (`from`). Land pattern as KiCad's
// D_SOD-123: 0.9 x 1.2 mm pads, 3.3 mm apart.

module.exports = {
  params: {
    designator: 'D',
    from: undefined,
    to: undefined,
  },
  body: p => `
    (module D_SOD-123 (layer B.Cu) (tedit 0)
      ${p.at /* parametric position */}
      (attr smd)
      (fp_text reference "${p.ref}" (at 0 -1.9 ${p.r}) (layer B.SilkS) ${p.ref_hide} (effects (font (size 0.8 0.8) (thickness 0.12)) (justify mirror)))
      (fp_text value "1N4148W" (at 0 1.9 ${p.r}) (layer B.Fab) hide (effects (font (size 0.8 0.8) (thickness 0.12)) (justify mirror)))
      ${'' /* cathode bar and body outline */}
      (fp_line (start -2.4 -0.95) (end -2.4 0.95) (layer B.SilkS) (width 0.2))
      (fp_line (start -2.4 -0.95) (end 1.1 -0.95) (layer B.SilkS) (width 0.12))
      (fp_line (start -2.4 0.95) (end 1.1 0.95) (layer B.SilkS) (width 0.12))
      (fp_line (start -1.35 -0.8) (end 1.35 -0.8) (layer B.Fab) (width 0.1))
      (fp_line (start 1.35 -0.8) (end 1.35 0.8) (layer B.Fab) (width 0.1))
      (fp_line (start 1.35 0.8) (end -1.35 0.8) (layer B.Fab) (width 0.1))
      (fp_line (start -1.35 0.8) (end -1.35 -0.8) (layer B.Fab) (width 0.1))
      (pad 1 smd rect (at -1.65 0 ${p.r}) (size 0.9 1.2) (layers B.Cu B.Paste B.Mask) ${p.to})
      (pad 2 smd rect (at 1.65 0 ${p.r}) (size 0.9 1.2) (layers B.Cu B.Paste B.Mask) ${p.from})
    )
  `,
}
