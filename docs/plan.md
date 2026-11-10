# Flatwell design plan

Last updated 2026-11-10.

## Goals

1. Advantage2-style split key layout and thumb clusters, so most of the muscle memory carries over.
2. Wireless (Bluetooth), ZMK firmware.
3. Much thinner than the Advantage2's ~73 mm. No concave wells: flat PCB, low-profile switches.
4. Built-in Magic Trackpad, laid out like a MacBook. (Touch ID is deferred to v2.)
5. **No bigger than a 16-inch MacBook Pro**, so it travels in the same Coach Austin Brief.
6. Buildable: our own PCB from PCBWay, 3D-printed case.

## Size limit: a 16-inch MacBook Pro

The keyboard goes in a Coach Austin Brief (14.75 × 10.5 × 2.25 in) with a 16-inch MacBook Pro,
so it must be **no bigger than the MacBook: 355.7 × 248.1 mm** (Apple spec, 2021 and later;
`bag_w`, `bag_h` in the config). `npm run build` fails past that.

The current layout is **354 × 246.7 mm**.

Thickness: the bag is 57 mm deep and the MacBook takes 16.8 mm. Aim for ≤ 25 mm.

## Layout (variant `macbook`)

- Two Advantage2-style halves with flat column stagger, 1.25u outer columns, Choc spacing
  (18 × 17 mm). 64 keys.
- **Hand spacing:** F–J is 174 mm (`center_gap` 120), the widest that fits. The Advantage2's
  is 229 mm, but that makes the board 417 mm wide.
- **No function row.** Dropping it paid for the thumb clusters.
- **Thumb clusters** in the Advantage2 spot, fanned 10° toward the middle:

  ```
  left:  [Bksp][Del][Ctrl]      right:  [Ctrl][Enter][Space]
         [Bksp][Del][End ]              [PgDn][Enter][Space]
  ```

  Bksp, Del, Enter and Space are 2u tall. Compared with the Advantage2, Alt, Home, Cmd and
  PgUp are gone (rarely used) and Ctrl moved down into Home's spot.
- **Esc** is where Caps Lock was. There's no Caps Lock.
- **Moved to a layer:** F1–F12, PrtSc, ScrLk, Pause, Keypad, Program, Alt/Option, Cmd, Home,
  PgUp.
- **Trackpad:** centered below the thumb clusters. `npm run build` places it one 4 mm rim
  below the lowest key above it. Palm rests on either side, like a MacBook.

### Layouts that didn't make it

- Trackpad between the halves (`center`, `raised`): 417 mm wide.
- Trackpad below full Kinesis thumb clusters, with an F row (`front`): ~290 mm deep.
- F row plus a flat MacBook-style thumb row: fit, but traded the thumb clusters for the F row.

## Electronics

Our own key PCB, wired straight to a nice!nano. No shift register.

- **One PCB**, 345 × 118 mm: a band under both halves, filled in between them down to 2 mm
  above the trackpad pocket (room for traces around the thumb clusters). Ergogen generates it with parts placed and nets assigned; `npm run route`
  routes it.
- **Matrix:** 10 rows × 7 columns, 17 GPIOs. Rows R0–R4 are the left half (num row to bottom
  row), R5–R9 the right. Columns C0 (outer) to C5 (inner) are shared by both halves; C6 is an
  extra column for thumb keys. Diodes are col2row: column → switch → diode → row.
- **Parts:** 64 Kailh Choc v1 switches in Kailh hotswap sockets, 64 SOD-123 diodes (1N4148W),
  a nice!nano v2, a JST-PH 2-pin battery connector, an SMD reset button and a LiPo. No power
  switch in v1; the firmware sleeps when idle.
- **7 M3 mounting holes** where there's no key (see the case section).
- **Everything but the switches is on the back** (hotswap sockets, diodes, nice!nano, battery
  connector, reset button), so the top of the board is flat under the case.
- **nice!nano placement:** on the back at the back edge between the halves, components facing
  down, USB end flush with the edge.

nice!nano pin map (pad numbers as in the footprint, `ergogen/footprints/nicenano.js`):

| Net | Pad | GPIO | | Net | Pad | GPIO |
| --- | --- | --- | --- | --- | --- | --- |
| R0 | 1 | P0.06 | | R5 | 15 | P1.11 |
| R1 | 2 | P0.08 | | R6 | 16 | P1.13 |
| R2 | 5 | P0.17 | | R7 | 17 | P1.15 |
| R3 | 6 | P0.20 | | R8 | 18 | P0.02 |
| R4 | 7 | P0.22 | | R9 | 19 | P0.29 |
| C0 | 8 | P0.24 | | C5 | 20 | P0.31 |
| C1 | 9 | P1.00 | | C6 | 14 | P0.10 |
| C2 | 10 | P0.11 | | spare | 13 | P0.09 |
| C3 | 11 | P1.04 | | spare | 31–33 | P1.01, P1.02, P1.07 |
| C4 | 12 | P1.06 | | | | |

Check before ordering the PCB:

- **nice!nano orientation:** it mounts underneath, components facing down, so the footprint is
  the mirror of the top-view pinout (from github.com/bstiq/nice-nano-kicad). Print the bottom of
  the PCB at 1:1 and set a real nice!nano on it, components down.
- **Switch and socket fit:** set a Choc switch with a hotswap socket on the same printout.

Checked 2026-11-10: C6 is on P0.10, an NFC antenna pin. ZMK's nice_nano board doesn't switch the
NFC pins to GPIO itself (the nice!nano's bootloader does), so our shield sets
`&uicr { nfct-pins-as-gpios; }` explicitly. Confirmed in the compiled devicetree.

Background: we started from [PillzMod](https://github.com/dcpedit/pillzmod), a replacement
controller board (nice!nano + 74HC595) for a real Kinesis, and its ZMK shield. Since we make our
own PCB, a direct matrix is simpler and needs no shift register, so we dropped compatibility.

## Magic Trackpad

- Apple spec (USB-C model): 160 × 114.9 mm, 4.9–10.9 mm tall wedge, 230 g.
- **Plan: drop in the whole, unopened unit.** It keeps its own Bluetooth, battery and
  Force Touch haptics, and lifts out for charging or replacement. The pocket is the spec size
  plus `tp_clear` (0.6 mm per side; tune after a test print).
- Its USB-C port is on the back edge, which faces the thumb clusters. Leave a channel for a short
  internal cable.
- It must sit landscape: macOS has no setting to rotate trackpad input.
- Thick edge at the back; its ~3° slope faces you, like a MacBook's palm rest.
- **Palm check:** at 174 mm hand spacing, palm heels overlap the trackpad's side edges a little,
  as on a MacBook. macOS ignores resting palms on MacBook trackpads; test whether the Magic
  Trackpad does too with the paper mockup and a real trackpad.

## Touch ID (deferred to v2)

Not in v1 (decided 2026-11-10): no opening in the case and no hole in the PCB. The notes
below are kept for v2, which would need a new case and a PCB with the hole back.

The Touch ID sensor is cryptographically paired to the Magic Keyboard's own logic board, so
it can't be wired to the nice!nano. The known approach (Khaos Tian, 2022; Snazzy Labs builds) is
to **transplant the Magic Keyboard logic board + Touch ID button + battery** from a donor
keyboard. It stays a separate Bluetooth keyboard that only has a Touch ID key.

- Needs an Apple silicon Mac. Pair it once over a cable, like a normal Magic Keyboard.
- The teardown is destructive and fiddly. Buy a used or broken donor; keyboard damage is fine as
  long as the logic board and sensor survive.
- Teardown guides cover the Lightning model. Check before buying a USB-C (2024) donor.
- **Sizes**, measured 2026-11-10 from Snazzy Labs' public-domain "Wireless TKL" enclosure
  (printables.com/model/320000), which holds the same parts from a no-numpad Magic Keyboard:
  - Bay for logic board + battery + button: **138 × 31 mm, about 5.2 mm deep**
    (the whole enclosure is 144 × 37 × 15.8 mm).
  - Button opening: **14.5 mm square** through a 3 mm top plate, narrowing to 10.5 mm at the
    surface. The button sits over the middle of the board (69.8 mm from one end).
  - Two 3 mm screw bosses, 50 mm apart, 4.7 mm off the button's center line.
- That enclosure was drawn for the Lightning keyboard. MakerWorld model 1128620 says the USB-C
  keyboard also works but ships a separate body for it, so its port area differs. Those files
  need a MakerWorld login; verify against a real donor before ordering the case.
- **Placement (v2):** the button stays directly over its board, so the 138 × 31 mm bay runs
  left-right under the right half's number row, in a layer **below the key PCB**. That adds
  about 6 mm under that part of the board. The numpad keyboard's longer board won't fit.

## Power and charging

There are two batteries: the nice!nano's LiPo and the trackpad's.
Option: one USB-C port on the case feeding a small internal USB 2.0 hub, with the nice!nano and
trackpad downstream. Plugging in one cable then charges both (and makes
them wired).

## Case and printing

- **PCBWay prints the case** (decided 2026-11-10), so it can be one piece per shell with no
  split lines. MJF nylon (PA12) is the default pick: strong, slightly flexible, matte.
- Rounded corners (12 mm radius), like the MacBook, so it slides into the bag.
- **Generated by `npm run case`** (`scripts/case.py`) from the layout, into
  `fab/macbook/flatwell-case-{tray,top}.stl`. Both shells are watertight; 354 × 246.7 × 13.6 mm
  assembled, keycap tops at about 20 mm.
- **Tray:** 2 mm floor, 2.5 mm wall to 9.6 mm. Posts with M3 heat-set inserts; 30 small posts
  hold the PCB up at 8.0 mm, placed clear of every socket, diode and the nice!nano. Sloped ribs
  carry the trackpad so its top is level and flush with the palm deck. Openings: USB notch at
  the back center, a push-out hole under the trackpad, a pin hole under the reset button.
- **Top:** a 2.2 mm key deck that rests on the PCB and doubles as the switch plate (1.2 mm lip,
  13.8 mm openings), and a 4 mm palm deck, hollowed underneath, around the trackpad pocket.
- **Screws:** 7 × M3×8 through the top and PCB, 8 × M3×6 in the palm area, into 15 inserts.
- The battery lies loose (taped) under a palm rest: 7.6 mm of height there.
- Unproven: MJF flatness over 354 mm, the plate lip's strength, and whether 6 mm under the PCB
  clears a nice!nano on standard headers (about 5.5 mm).
- Tenting: not planned. It has to lie flat in the bag.

## Fab: PCBWay

`npm run route` does the whole trip in about 5 minutes: Freerouting autoroutes
`output/macbook/flatwell.kicad_pcb` (usage data and network servers off), KiCad checks the
result (DRC) and writes the files below. Latest run (2026-11-10): fully routed, 0 DRC errors,
47 vias, 0.25 mm traces necked to 0.19 mm between pads. The only DRC warnings are silkscreen
touching pads or the board edge (cosmetic; PCBWay trims silkscreen off pads).

Router settings that matter (in `scripts/route.sh`): fanout off (it added a via at every SMD
pad), neckdown on (traces need it to pass between switch pads), 0.5 mm copper-to-edge.

- `fab/macbook/flatwell-gerbers.zip`: upload to PCBWay. 2 layers, 345 × 118 mm, 1.6 mm FR-4,
  HASL lead-free, any solder mask color.
- `fab/macbook/flatwell-bom.csv` and `flatwell-cpl.csv`: for PCBWay's assembly service, which
  can place the 64 diodes (bottom side). Hotswap sockets, nice!nano, battery connector and reset
  button are easy to hand-solder.
- `output/macbook/flatwell-routed.kicad_pcb`: the routed board, to inspect or tweak in KiCad.

## Firmware

`npm run firmware` generates our ZMK shield into `firmware/` and builds `firmware/flatwell.uf2`
locally (first run downloads ZMK, Zephyr and the ARM toolchain into `tools/`, about 3 GB).
Builds clean as of 2026-11-10: 28% of flash, ZMK Studio enabled.

- Pins come from the PCB section of `ergogen/config.yaml` and the matrix from `points.json`, so
  firmware and board can't drift apart. The compiled pin list matches the table above.
- Physical layout from the key positions, so ZMK Studio shows the real shape.
- **Base layer** from `scripts/legends.mjs`: Esc in Caps Lock's spot, and **Fn where Insert was**
  (the board needs one layer key).
- **Fn layer:** number row = F1–F10, `=` F11, `-` F12; arrows = Home/End/PgUp/PgDn;
  thumb Ctrl keys = Option (left) and Cmd (right); Bksp = Cmd, Space = Option;
  Q/W/E/R = Bluetooth profiles 1–4, T = clear profile, Y = USB/Bluetooth toggle, P = PrtSc;
  Tab = unlock ZMK Studio, `\` = bootloader (for flashing).
- **Open:** Cmd and Option are only on Fn right now, which is awkward on a Mac. Remap live in
  ZMK Studio, or tell me where they should go.
- `firmware/` is also a valid zmk-config repo (`build.yaml`, `config/west.yml`) if you'd rather
  build with GitHub Actions.
- To flash: plug the nice!nano in over USB, double-tap reset, drag `flatwell.uf2` onto the
  drive that appears.

Studio support also means the board could be added to Remap360's browser editor later.

## Decisions so far

| Decision | Choice | Why |
| --- | --- | --- |
| Generator | Ergogen | Flat layouts, PCB + outline output, scriptable |
| Switches | Choc v1, hotswap sockets | Thinnest common option; user wants hotswap |
| Electronics | Own PCB, direct 10 × 7 matrix on a nice!nano | Simpler than PillzMod's shift register |
| Layout | MacBook style: trackpad below the thumb clusters | User's pick; fits the size limit |
| Size limit | 355.7 × 248.1 mm (16-in MacBook Pro) | Travels in the same bag as the MacBook |
| Hand spacing | F–J 174 mm | Widest that fits |
| F row | None; F keys on a layer | Room for the thumb clusters |
| Esc | Caps Lock's spot; no Caps Lock | User's pick |
| Thumb keys | Bksp, Del, Ctrl, End / PgDn, Ctrl, Enter, Space | User doesn't use Alt/Home/Cmd/PgUp much |
| Case | 3D printed by PCBWay, unsplit | No printer big enough at home |
| Trackpad | Whole unit, drop-in | No teardown, keeps Force Touch + battery |
| Touch ID | Not in v1 | Simpler, thinner case; revisit for v2 |

## Open questions

1. Internal USB hub for one-port charging: worth the extra board?

## Next steps

1. Print `preview/print.html`, tape it up, put a real Magic Trackpad on it, and type on it.
2. Print `fab/macbook/flatwell-print.html` (the PCB's back at 1:1) and check a real nice!nano,
   a Choc switch and a hotswap socket against it. Then order from PCBWay.
3. Order from [ORDER.md](../ORDER.md) once the two print checks pass.

## References

- Ergogen: https://ergogen.xyz
- nice!nano: https://nicekeyboards.com/nice-nano
- nice!nano KiCad footprint (pad positions): https://github.com/bstiq/nice-nano-kicad
- PillzMod (where we started): https://github.com/dcpedit/pillzmod
- Magic Trackpad specs: https://support.apple.com/en-bh/121932
- 16-inch MacBook Pro specs: https://support.apple.com/111901
- Coach Austin Brief: https://www.coach.com/products/austin-brief/CFG68.html
- Snazzy Labs standalone Touch ID enclosure (bay sizes): https://www.printables.com/model/320000-standalone-touch-id-module-for-mac
- Hidden Touch ID for Magic Trackpad (Lightning + USB-C notes): https://makerworld.com/models/1128620
- Standalone Touch ID teardown (Khaos Tian): https://gist.github.com/KhaosT/1406a6b6bea38f59e059c2afcb39d545
- Standalone Touch ID writeups: https://hackaday.com/2022/12/26/standalone-touch-id-for-your-desktop-mac/ ,
  https://www.jeffgeerling.com/blog/2025/why-doesnt-apple-make-standalone-touch-id/
