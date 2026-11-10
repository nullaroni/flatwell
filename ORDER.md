# Flatwell v1: what to order

Everything needed to build one keyboard. The files are in [`fab/macbook/`](fab/macbook/).

> **Status: untested prototype.** No board or case has been made yet. The PCB passes KiCad's
> design-rule check and the firmware compiles, but nothing has been checked against real parts.
> Do the [checks](#before-ordering) first. Expect that v1 may need a second revision.

## Before ordering

1. Print [`fab/macbook/flatwell-print.html`](fab/macbook/flatwell-print.html) at 100% (it is
   the back of the PCB at true size). Measure the 50 mm bar.
2. Lay a nice!nano on its outline (chips facing you, USB at the board edge), and a Choc switch
   with a hotswap socket on one key position. Everything must line up with the pads and holes.
3. Print [`preview/print.html`](preview/print.html), tape the halves, set a Magic Trackpad on
   it and try the key positions with your hands.

## 1. PCB (PCBWay, "PCB Instant Quote")

Upload [`fab/macbook/flatwell-gerbers.zip`](fab/macbook/flatwell-gerbers.zip).

| Option | Value |
| --- | --- |
| Size | 345 × 118.3 mm (PCBWay reads it from the file) |
| Layers | 2 |
| Quantity | 5 (the minimum) |
| Material / thickness | FR-4, 1.6 mm |
| Min track / spacing | 6/6 mil (the board's narrowest track is 0.15 mm, spacing 0.2 mm) |
| Min hole | 0.3 mm |
| Solder mask / silkscreen | any color |
| Surface finish | HASL lead-free |
| Copper | 1 oz |
| Everything else | default |

**Optional assembly** (saves hand-soldering 64 small diodes): choose "Assembly", bottom side
only, and upload [`flatwell-bom.csv`](fab/macbook/flatwell-bom.csv) and
[`flatwell-cpl.csv`](fab/macbook/flatwell-cpl.csv). The only assembled part is D1–D64,
1N4148W in SOD-123. Ask PCBWay to confirm diode direction against the silkscreen: the thick bar
marks the cathode. All other parts are hand-soldered.

## 2. Case (PCBWay, "3D Printing")

Upload both files, quantity 1 each:

| File | Part | Size |
| --- | --- | --- |
| [`flatwell-case-tray.stl`](fab/macbook/flatwell-case-tray.stl) | bottom tray | 354 × 246.7 × 9.6 mm, 218 cm³ |
| [`flatwell-case-top.stl`](fab/macbook/flatwell-case-top.stl) | top shell | 354 × 246.7 × 4.0 mm, 136 cm³ |

| Option | Value |
| --- | --- |
| Units | millimetres |
| Process / material | MJF, PA12 nylon (HP) |
| Color | black (dyed), or natural gray |
| Finish | standard (bead blasted) |
| Threads / inserts | none (inserts are added by hand, below) |

Notes for the printer: the thinnest feature is the 1.2 mm switch plate lip around each 13.8 mm
key opening; keep those openings to size. Both parts are large and flat, so ask them to orient
the parts to limit warping, and to say so before printing if they expect more than 1 mm of bow.

## 3. Parts

| Qty | Part | Notes |
| --- | --- | --- |
| 1 | nice!nano v2 | With its pin headers. Mounts on the back of the PCB, chips facing away from it. |
| 64 | Kailh Choc v1 switches | Any Choc **v1** type. Not Choc v2, not MX. Buy ~70. |
| 64 | Kailh Choc hotswap sockets (CPG135001S30) | Buy ~70. |
| 64 | 1N4148W diodes, SOD-123 | Skip if PCBWay assembles them. |
| 60 | Choc v1 keycaps, 1u, 18 × 17 mm spacing (e.g. MBK) | 8 of these go on the 1.25u-wide outer columns. |
| 4 | Choc v1 keycaps, 2u (e.g. MBK 2u) | Thumb keys, mounted vertically. No stabilizers. |
| 1 | LiPo battery, 3.7 V, JST-PH 2.0 mm plug, at most 6 mm thick | e.g. a 503450 (5 × 34 × 50 mm, ~1000 mAh). **Check polarity** against the nice!nano before plugging in: many batteries are wired the other way round. |
| 1 | JST-PH 2-pin right-angle header (S2B-PH-K) | Through-hole. |
| 1 | SMD tactile switch, 6 × 3.7 mm, 2 pads (Alps SKQG type) | Reset button. Optional. |
| 15 | M3 heat-set inserts, 4.6 mm outer diameter, 4–5.7 mm long | Pressed into the tray posts with a soldering iron. |
| 7 | M3 × 8 mm button-head screws | Through the top shell and PCB. |
| 8 | M3 × 6 mm button-head screws | Palm area. |
| 1 | Apple Magic Trackpad, 160 × 114.9 mm (Magic Trackpad 2 or later, Lightning or USB-C) | Drops into the pocket; it stays its own Bluetooth device. |
| 4–6 | Stick-on rubber feet, about 2 mm tall | |

## 4. Firmware

[`firmware/flatwell.uf2`](firmware/flatwell.uf2) is ready to flash (rebuild it with `npm run firmware`). Plug the
nice!nano in over USB, double-tap reset, and drag the file onto the drive that appears. Keys can
be remapped afterwards in [ZMK Studio](https://zmk.studio).

## Known limits of v1

- No power switch: the keyboard sleeps after 15 minutes idle and wakes on any key. Unplug the
  battery for long storage.
- The trackpad's own power switch and charging port are covered while it's in the pocket. Push
  it out through the hole in the tray to charge it.
- No Touch ID.
- Keycap tops end up about 20 mm above the desk; the case alone is 13.6 mm.
