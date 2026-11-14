#!/usr/bin/env python3
"""Stamp the Nullworks mark onto the flatwell back silkscreen.

The mark is the slashed zero: the ring with the wide cream band cut out (that
band is bare board, not ink) and the thin slash left in the gap. It is a
footprint on B.SilkS, 10 mm tall, with "NULLWORKS", "flatwell v1" and "2026"
beside it. Nothing electrical moves.

Idempotent. scripts/route.sh runs this on the routed board before DRC and the
fab export. Safe to run by hand:

    python3 scripts/silk_logo.py fab/macbook/flatwell.kicad_pcb
"""
import sys

# Footprint anchor is the center of the mark-plus-wording group.
# Board position (0, -37.4): the open channel between the key halves, under
# the nice!nano and above the center mounting hole, battery connector and
# reset button.
FOOTPRINT = """\
	(footprint "Nullworks_Logo"
		(layer "B.Cu")
		(uuid "5cade583-6459-4ea7-b7e4-13283452eec5")
		(at 0 -37.4)
		(property "Reference" "LOGO1"
			(at 0 0 0)
			(layer "F.SilkS")
			(hide yes)
			(uuid "a2e198bb-9daa-451d-a929-e0c1dfe9bb1d")
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Value" "Nullworks"
			(at 0 0 0)
			(layer "F.Fab")
			(hide yes)
			(uuid "16a70dec-38a8-4d9e-bb3b-e2d7781287aa")
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Datasheet" ""
			(at 0 0 0)
			(layer "F.Fab")
			(hide yes)
			(uuid "97327f9c-715e-41f0-b22e-7bef14e9e784")
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Description" ""
			(at 0 0 0)
			(layer "F.Fab")
			(hide yes)
			(uuid "0c45e653-7b54-4dee-b897-c01b468b30e6")
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(attr board_only exclude_from_pos_files exclude_from_bom)
		(duplicate_pad_numbers_are_jumpers no)
		(fp_poly
			(pts
				(xy 8.0889 -5) (xy 8.8498 -5) (xy 12.6541 5) (xy 11.8932 5)
			)
			(stroke
				(width 0.15)
				(type default)
			)
			(fill yes)
			(layer "B.SilkS")
			(uuid "101bf59d-2b95-4a11-95a4-799b2cd8b5db")
		)
		(fp_poly
			(pts
				(xy 10.3715 4.5652) (xy 10.083 4.5499) (xy 9.8048 4.5049) (xy 9.5373 4.4313) (xy 9.2811 4.3304)
				(xy 9.0366 4.2035) (xy 8.8043 4.051599) (xy 8.5848 3.8762) (xy 8.3785 3.6783) (xy 8.1858 3.4592)
				(xy 8.0074 3.2201) (xy 7.8436 2.9623) (xy 7.695 2.687) (xy 7.562 2.3953) (xy 7.4452 2.0886) (xy 7.345 1.768)
				(xy 7.2619 1.4348) (xy 7.1965 1.0901) (xy 7.1491 0.7353) (xy 7.1203 0.3715) (xy 7.1106 0) (xy 7.1203 -0.3715)
				(xy 7.1491 -0.7353) (xy 7.1965 -1.0901) (xy 7.2619 -1.4348) (xy 7.345 -1.768) (xy 7.4452 -2.0886)
				(xy 7.562 -2.3953) (xy 7.695 -2.687) (xy 7.8436 -2.9623) (xy 8.0074 -3.2201) (xy 8.1858 -3.4592)
				(xy 8.9789 -1.3748) (xy 8.9628 -1.2361) (xy 8.9371 -0.9412) (xy 8.9188 -0.6363) (xy 8.9078 -0.3223)
				(xy 8.9041 0) (xy 8.9078 0.3223) (xy 8.9188 0.6363) (xy 8.9371 0.9412) (xy 8.9628 1.2361) (xy 8.9958 1.52)
				(xy 9.0362 1.7922) (xy 9.0839 2.0516) (xy 9.1389 2.2974) (xy 9.2013 2.5287) (xy 9.271 2.7446) (xy 9.348 2.9441)
				(xy 9.4324 3.1265) (xy 9.5241 3.2908) (xy 9.6231 3.4361) (xy 9.7295 3.5615) (xy 9.8432 3.6661) (xy 9.9643 3.749)
				(xy 10.0927 3.8093) (xy 10.2284 3.8462) (xy 10.3715 3.8587) (xy 10.5146 3.8462) (xy 10.6503 3.8093)
				(xy 10.7787 3.749) (xy 10.8973 3.6678) (xy 11.1895 4.4358) (xy 10.9382 4.5049) (xy 10.66 4.5499)
			)
			(stroke
				(width 0.15)
				(type default)
			)
			(fill yes)
			(layer "B.SilkS")
			(uuid "190e2bb5-e4a9-4c58-ab92-4e2f72770f33")
		)
		(fp_poly
			(pts
				(xy 11.2057 -4.4313) (xy 11.4619 -4.3304) (xy 11.7064 -4.2035) (xy 11.9387 -4.051599) (xy 12.1582 -3.8762)
				(xy 12.3645 -3.6783) (xy 12.5572 -3.4592) (xy 12.7356 -3.2201) (xy 12.8994 -2.9623) (xy 13.048 -2.687)
				(xy 13.181 -2.3953) (xy 13.2978 -2.0886) (xy 13.398 -1.768) (xy 13.4811 -1.4348) (xy 13.5465 -1.0901)
				(xy 13.5939 -0.7353) (xy 13.6227 -0.3715) (xy 13.6324 0) (xy 13.6227 0.3715) (xy 13.5939 0.7353)
				(xy 13.5465 1.0901) (xy 13.4811 1.4348) (xy 13.398 1.768) (xy 13.2978 2.0886) (xy 13.181 2.3953)
				(xy 13.048 2.687) (xy 12.8994 2.9623) (xy 12.7356 3.2201) (xy 12.5572 3.4592) (xy 11.7641 1.3748)
				(xy 11.7802 1.2361) (xy 11.8059 0.9412) (xy 11.8242 0.6363) (xy 11.8352 0.3223) (xy 11.8389 0) (xy 11.8352 -0.3223)
				(xy 11.8242 -0.6363) (xy 11.8059 -0.9412) (xy 11.7802 -1.2361) (xy 11.7472 -1.52) (xy 11.7068 -1.7922)
				(xy 11.6591 -2.0516) (xy 11.6041 -2.2974) (xy 11.5417 -2.5287) (xy 11.472 -2.7446) (xy 11.395 -2.9441)
				(xy 11.3106 -3.1265) (xy 11.2189 -3.2908) (xy 11.1199 -3.4361) (xy 11.0135 -3.5615) (xy 10.8998 -3.6661)
				(xy 10.7787 -3.749) (xy 10.6503 -3.8093) (xy 10.5146 -3.8462) (xy 10.3715 -3.8587) (xy 10.2284 -3.8462)
				(xy 10.0927 -3.8093) (xy 9.9643 -3.749) (xy 9.8457 -3.6678) (xy 9.5535 -4.4358) (xy 9.8048 -4.5049)
				(xy 10.083 -4.5499) (xy 10.3715 -4.5652) (xy 10.66 -4.5499) (xy 10.9382 -4.5049)
			)
			(stroke
				(width 0.15)
				(type default)
			)
			(fill yes)
			(layer "B.SilkS")
			(uuid "1650b81e-e3da-4207-ac9a-dd114f533997")
		)
		(fp_text user "2026"
			(at -10.1754 1.55 0)
			(layer "B.SilkS")
			(uuid "f2e6d4f7-0bf4-4ec8-af9c-ff43baab47a0")
			(effects
				(font
					(size 1.3 1.3)
					(thickness 0.18)
				)
				(justify mirror)
			)
		)
		(fp_text user "NULLWORKS"
			(at -4.3609 -1.1 0)
			(layer "B.SilkS")
			(uuid "67faf75b-8ae9-4e7d-8efa-006d70222ab2")
			(effects
				(font
					(size 2.2 2.2)
					(thickness 0.3)
				)
				(justify mirror)
			)
		)
		(fp_text user "flatwell v1"
			(at -1.3014 1.55 0)
			(layer "B.SilkS")
			(uuid "7d218687-283d-4813-82ff-727de4fc97ea")
			(effects
				(font
					(size 1.3 1.3)
					(thickness 0.18)
				)
				(justify mirror)
			)
		)
		(embedded_fonts no)
	)
"""

NEEDLE = "\n\t(gr_line\n\t\t(start -172.5 -83.5)\n"


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: silk_logo.py <board.kicad_pcb>")
    path = sys.argv[1]
    text = open(path).read()
    if 'footprint "Nullworks_Logo"' in text:
        print(f"Nullworks logo already on {path}")
        return
    if NEEDLE not in text:
        sys.exit(f"{path}: could not find the board-outline insertion point")
    text = text.replace(NEEDLE, "\n" + FOOTPRINT + NEEDLE[1:], 1)
    open(path, "w").write(text)
    print("Nullworks logo on B.SilkS at (0, -37.4) mm, mark 6.52 x 10.00 mm")


if __name__ == "__main__":
    main()
