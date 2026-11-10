# Flatwell

A flat, low-profile, wireless keyboard based on the Kinesis Advantage2, laid out like a
MacBook: keys on top, a built-in Apple Magic Trackpad centered below them. It's no bigger than a 16-inch MacBook Pro, so it travels in the
same bag.

- **Layout:** the Advantage2's split key layout with column stagger and no concave wells,
  64 Kailh Choc v1 low-profile switches. No function row; Advantage2-style thumb clusters
  (2u Bksp/Del and Enter/Space, plus Ctrl and End/PgDn) right above the trackpad.
- **Size:** 354 × 247 mm, inside a 16-inch MacBook Pro's footprint (355.7 × 248.1 mm). The
  build fails if it grows past that.
- **Electronics:** our own PCB, a 10 × 7 key matrix wired straight to a nice!nano (17 pins),
  running ZMK.
- **Trackpad:** a whole Magic Trackpad drops into a pocket. (Touch ID is deferred to v2.)
- **Fab:** PCB from PCBWay (Ergogen generates it, KiCad routes it); the case is 3D printed.

Status: **untested v1 prototype**. The board is routed, the firmware builds and the case is
modelled, but nothing has been made yet. What to order is in [ORDER.md](ORDER.md); the design,
decisions and open questions are in [docs/plan.md](docs/plan.md).

## Build

```sh
npm install
npm run build     # → preview/index.html, preview/print.html, output/<variant>/…
                  #   output/macbook/flatwell.kicad_pcb: unrouted PCB, open in KiCad
```

Then route the PCB and make the PCBWay files (needs KiCad, Java and Freerouting; see the
top of `scripts/route.sh`):

```sh
npm run route     # → output/macbook/flatwell-routed.kicad_pcb, fab/macbook/flatwell-gerbers.zip
```

Then the firmware (needs `brew install cmake ninja dtc uv`; first run downloads about 3 GB):

```sh
npm run firmware  # → firmware/flatwell.uf2 (ZMK, with ZMK Studio)
```

And the case shells (needs `uv`):

```sh
npm run case      # → fab/macbook/flatwell-case-{tray,top}.stl
```

`preview/print.html` prints each half on a Letter page (portrait) at 1:1. Tape the halves
together at the red center line, set a real Magic Trackpad on the outline, and try your
hands on it.

The build fails if:

- a key has no legend or no matrix position, or two keys share a position
- on the PCB, a key's switch and diode aren't wired to each other, or a row or column
  doesn't reach the nice!nano
- a keycap overlaps another key or comes within the rim of the trackpad pocket
- the case outgrows the size limit (`bag_w` × `bag_h`)

- `ergogen/config.yaml`: the parametric layout ([Ergogen](https://ergogen.xyz) v4)
- `ergogen/variants.yaml`: per-variant overrides
- `ergogen/footprints/`: nice!nano (including its 3 middle pins) and back-side SOD-123 diode footprints
- `scripts/build.mjs`: runs Ergogen per variant, places the trackpad, runs the checks,
  renders the previews
- `scripts/legends.mjs`: key legends by key name
- `scripts/case.py`: builds the two case shells from the layout
- `scripts/zmk.mjs`, `scripts/firmware.sh`: generate the ZMK shield in `firmware/` and build it
- `scripts/route.sh`, `scripts/pcb_print.py`, `scripts/kicad_route.py`: autoroute with Freerouting, DRC and fab files via KiCad
