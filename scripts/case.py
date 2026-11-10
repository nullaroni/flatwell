"""Builds the two case shells for 3D printing (PCBWay, MJF nylon).

  uv run --with trimesh --with shapely --with manifold3d --with mapbox-earcut --with numpy \\
      scripts/case.py [variant]          (or: npm run case)

Reads output/<variant>/{points.json,case.json,flatwell.kicad_pcb}; writes
fab/<variant>/flatwell-case-{tray,top}.stl and case-report.json.

How it goes together (z = 0 is the desk, all mm):

  tray  floor 0-2, outer wall up to 9.6. Posts hold M3 heat-set inserts. The PCB
        sits on posts with its underside at 8.0 (6 mm for sockets and the nice!nano).
        Sloped ribs carry the Magic Trackpad so its top is level.
  PCB   8.0-9.6. Only switches on top.
  top   key deck 9.6-11.8, resting on the PCB; it is also the switch plate (1.2 mm
        lip, 13.8 mm holes). The palm deck around the trackpad is 13.6 high.
  M3 screws go down through the top (and the PCB, in the key area) into the inserts.
"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "macbook"
OUT = ROOT / "output" / VARIANT
FAB = ROOT / "fab" / VARIANT

# --- heights -----------------------------------------------------------------
FLOOR = 2.0
PCB_BOTTOM = 8.0          # floor + 6.0: hotswap sockets (1.9) and nice!nano on headers (~5.7)
PCB_T = 1.6
DECK_BOTTOM = PCB_BOTTOM + PCB_T   # 9.6: the top shell rests on the PCB and the wall
PLATE_T = 1.2             # Choc v1 clips into a 1.2 mm plate...
DECK_TOP = DECK_BOTTOM + 2.2       # ...whose top is 2.2 mm above the PCB
TP_BACK, TP_FRONT = 10.9, 4.9      # Magic Trackpad thickness, back and front edge (Apple spec)
TP_FEET = 0.6             # its rubber feet
PALM_TOP = FLOOR + 0.1 + TP_FEET + TP_BACK   # 13.6: trackpad top is flush with the palm deck
PALM_SKIN = 2.4

# --- plan sizes ----------------------------------------------------------------
WALL = 2.5
CORNER = 12.0
SWITCH_HOLE = 13.8
SWITCH_RELIEF = 15.0      # room under the plate lip for the switch's clips
SCREW_HOLE = 3.4          # M3 clearance
SCREW_HEAD = 6.5          # counterbore in the palm deck (button head 5.7)
INSERT_HOLE = 4.0         # M3 heat-set insert, 4.6 mm knurl
INSERT_DEPTH = 6.0
POST_D = 7.5
SUPPORT_D = 3.5
SUPPORT_SPACING = 26.0
POCKET_WALL = 2.5
RIB_T, RIB_X = 2.4, (12, 32, 52, 72)
USB_SLOT_W, USB_SLOT_DEPTH = 14.0, 9.0

points = json.loads((OUT / "points.json").read_text())
cfg = json.loads((OUT / "case.json").read_text())
u, bx, tp = cfg["units"], cfg["box"], cfg["tp"]
pcb_text = (OUT / "flatwell.kicad_pcb").read_text()


def circle(x, y, d):
    return Point(x, y).buffer(d / 2, quad_segs=12)


def key_rect(k, w, h, dx=0.0, dy=0.0):
    """A w x h rectangle at offset (dx, dy) in the key's own frame (y up)."""
    r = box(dx - w / 2, dy - h / 2, dx + w / 2, dy + h / 2)
    return affinity.translate(affinity.rotate(r, k["r"], origin=(0, 0)), k["x"], k["y"])


def many(shapes):
    return unary_union(list(shapes))


# --- 2D regions (Ergogen coordinates: x right, y away from you) ------------------
case = box(bx["x0"] + CORNER, bx["y0"] + CORNER, bx["x1"] - CORNER, bx["y1"] - CORNER).buffer(CORNER, quad_segs=10)
inside = case.buffer(-WALL)

pcb = many(
    [
        box(-u["pcb_w"] / 2, u["pcb_bot"], u["pcb_w"] / 2, u["pcb_top"]),
        box(-u["pcb_mid_w"] / 2, u["pcb_low"] - 0.5, u["pcb_mid_w"] / 2, u["pcb_bot"] + 0.5),
    ]
    + [key_rect(k, k["w"] + 2, k["h"] + 2) for k in points if "thumb" in k["name"]]
)
pocket = box(tp["cx"] - tp["w"] / 2 + 6, tp["cy"] - tp["h"] / 2 + 6, tp["cx"] + tp["w"] / 2 - 6, tp["cy"] + tp["h"] / 2 - 6).buffer(6, quad_segs=8)
pocket_ring = pocket.buffer(POCKET_WALL).difference(pocket)

# Mounting holes come from the PCB file (KiCad's y axis points the other way).
mounts = [(float(x), -float(y)) for x, y in re.findall(r"\(module MountingHole_M3.*?\(at ([-\d.]+) ([-\d.]+)", pcb_text, re.S)]
assert len(mounts) == 7, f"expected 7 PCB mounting holes, found {len(mounts)}"

# Palm-area screws: front corners, sides, and either side of the trackpad.
sx, sy = bx["x1"] - 14, bx["y0"] + 14
palm_screws = [(s * x, y) for s in (-1, 1) for x, y in ((sx, sy), (sx, -42.0), (98.0, bx["y0"] + 12), (98.0, -30.0))]

front = box(bx["x0"], bx["y0"], bx["x1"], u["pcb_bot"] - 1.0)
palm = many([front.difference(pcb.buffer(1.0)), pocket.buffer(3.0)]).intersection(case)
key_deck = case.difference(palm)

switch_holes = many(key_rect(k, SWITCH_HOLE, SWITCH_HOLE) for k in points)
switch_reliefs = many(key_rect(k, SWITCH_RELIEF, SWITCH_RELIEF) for k in points)
all_screws = mounts + palm_screws
screw_holes = many(circle(x, y, SCREW_HOLE) for x, y in all_screws)

# What hangs under the PCB, so support posts can avoid it.
mcu = box(-10.5, u["pcb_top"] - 36.5, 10.5, u["pcb_top"] + 1)
under_pcb = many(
    [key_rect(k, 15.2, 8.0, dx=2.5, dy=4.85) for k in points]          # hotswap socket and its pads
    + [key_rect(k, 5.2, 2.4, dy=-5.0) for k in points]                 # diode
    + [affinity.translate(affinity.rotate(circle(dx, 0, d), k["r"], origin=(0, 0)), k["x"], k["y"])
       for k in points for dx, d in ((0, 4.6), (-5.5, 3.0), (5.5, 3.0))]  # switch post and legs
    + [mcu, box(-36.5, 23, -23.5, 37), box(24, 24.5, 36, 35.5)]         # nice!nano, battery plug, reset
    + [circle(x, y, POST_D) for x, y in mounts]
)


def pick_supports():
    """Posts under the PCB, spread out, each clear of every part by 1 mm."""
    free = pcb.buffer(-2.5).difference(under_pcb.buffer(SUPPORT_D / 2 + 1.0))
    x0, y0, x1, y1 = pcb.bounds
    cands = [(x, y) for x in np.arange(x0, x1, 1.5) for y in np.arange(y0, y1, 1.5) if free.contains(Point(x, y))]
    chosen = list(mounts)
    picked = []
    while True:
        best, best_d = None, SUPPORT_SPACING
        for c in cands:
            d = min(math.dist(c, p) for p in chosen)
            if d > best_d:
                best, best_d = c, d
        if best is None:
            return picked
        chosen.append(best)
        picked.append(best)


supports = pick_supports()

# --- 2.5D solids -----------------------------------------------------------------


def slab(shape, z0, z1):
    """Extrude a shapely (multi)polygon from z0 to z1."""
    polys = [shape] if isinstance(shape, Polygon) else list(shape.geoms)
    out = []
    for p in polys:
        if p.is_empty or p.area < 1e-6:
            continue
        m = trimesh.creation.extrude_polygon(p, z1 - z0)
        m.apply_translation((0, 0, z0))
        out.append(m)
    return out


def union(meshes):
    m = trimesh.boolean.union(meshes, engine="manifold")
    assert m.is_watertight, "shell is not watertight"
    return m


def rib(x):
    """A wedge the trackpad rests on: low at the back, high at the front."""
    _, y_front, _, y_back = pocket.bounds
    z_back = PALM_TOP - TP_FEET - TP_BACK
    z_front = PALM_TOP - TP_FEET - TP_FRONT
    side = Polygon([(y_front, FLOOR - 0.1), (y_back, FLOOR - 0.1), (y_back, z_back), (y_front, z_front)])
    m = trimesh.creation.extrude_polygon(side, RIB_T)          # (y, z, x) in local axes
    m.apply_transform(np.array([[0, 0, 1, x - RIB_T / 2], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float))
    return m


usb_slot = box(-USB_SLOT_W / 2, bx["y1"] - USB_SLOT_DEPTH, USB_SLOT_W / 2, bx["y1"] + 1)
push_hole = circle(tp["cx"], tp["cy"], 20)
reset_hole = circle(30, 30, 3)
wall = case.difference(inside)
key_posts = many(circle(x, y, POST_D) for x, y in mounts)
palm_posts = many(circle(x, y, POST_D) for x, y in palm_screws)
insert_holes = many(circle(x, y, INSERT_HOLE) for x, y in all_screws)

tray = union(
    slab(case.difference(many([usb_slot, push_hole, reset_hole])), 0, FLOOR)
    + slab(wall.difference(usb_slot), FLOOR, PCB_BOTTOM)
    + slab(wall, PCB_BOTTOM, DECK_BOTTOM)
    + slab(key_posts.difference(insert_holes), FLOOR, PCB_BOTTOM)
    + slab(palm_posts, FLOOR, DECK_BOTTOM - INSERT_DEPTH)
    + slab(palm_posts.difference(insert_holes), DECK_BOTTOM - INSERT_DEPTH, DECK_BOTTOM)
    + slab(many(circle(x, y, SUPPORT_D) for x, y in supports), FLOOR, PCB_BOTTOM)
    + slab(pocket_ring, FLOOR, PCB_BOTTOM)
    + slab(pocket_ring.difference(pcb.buffer(0.6)), PCB_BOTTOM, DECK_BOTTOM)
    + [rib(s * x) for s in (-1, 1) for x in RIB_X]
)

palm_solid = palm.difference(pocket)
cavity = palm.buffer(-3.0).difference(many([pocket.buffer(6.0)] + [circle(x, y, 10) for x, y in palm_screws]))
counterbores = many(circle(x, y, SCREW_HEAD) for x, y in palm_screws)
top = union(
    slab(key_deck.difference(many([switch_reliefs, screw_holes])), DECK_BOTTOM, DECK_TOP - PLATE_T)
    + slab(key_deck.difference(many([switch_holes, screw_holes])), DECK_TOP - PLATE_T, DECK_TOP)
    + slab(palm_solid.difference(many([cavity, screw_holes])), DECK_BOTTOM, PALM_TOP - PALM_SKIN)
    + slab(palm_solid.difference(screw_holes), PALM_TOP - PALM_SKIN, PALM_TOP - 1.8)
    + slab(palm_solid.difference(counterbores), PALM_TOP - 1.8, PALM_TOP)
)

# --- checks and output -------------------------------------------------------------
problems = []
for x, y in mounts:
    if not pcb.buffer(-3.0).contains(Point(x, y)):
        problems.append(f"PCB screw at ({x}, {y}) is within 3 mm of the PCB edge")
    if under_pcb.difference(circle(x, y, POST_D)).distance(Point(x, y)) < POST_D / 2 + 0.3:
        problems.append(f"post at ({x}, {y}) touches a part under the PCB")
    if switch_reliefs.distance(Point(x, y)) < SCREW_HOLE / 2 + 0.8:
        problems.append(f"screw at ({x}, {y}) is too close to a switch hole")
for x, y in palm_screws:
    if not palm.buffer(-POST_D / 2).contains(Point(x, y)) or pocket.buffer(POCKET_WALL).distance(Point(x, y)) < POST_D / 2:
        problems.append(f"palm screw at ({x}, {y}) is off the palm deck or in the trackpad wall")
    if pcb.distance(Point(x, y)) < POST_D / 2 + 0.5:
        problems.append(f"palm post at ({x}, {y}) hits the PCB")
if PALM_TOP - TP_FEET - TP_BACK < FLOOR:
    problems.append("trackpad pocket is deeper than the floor")
size = np.round(np.maximum(tray.bounds[1], top.bounds[1]) - np.minimum(tray.bounds[0], top.bounds[0]), 2)
if size[0] > u["bag_w"] or size[1] > u["bag_h"]:
    problems.append(f"case is {size[0]} x {size[1]} mm, over the {u['bag_w']} x {u['bag_h']} limit")

FAB.mkdir(parents=True, exist_ok=True)
# STL in print orientation: x right, y back, z up; each shell flat on its largest face.
tray.export(FAB / "flatwell-case-tray.stl")
top_print = top.copy()
top_print.apply_translation((0, 0, -DECK_BOTTOM))
top_print.export(FAB / "flatwell-case-top.stl")

report = {
    "size_mm": {"width": size[0], "depth": size[1], "height_without_keys": size[2], "keycap_top_approx": round(DECK_BOTTOM + 10.5, 1)},
    "tray": {"volume_cm3": round(tray.volume / 1000, 1), "watertight": bool(tray.is_watertight)},
    "top": {"volume_cm3": round(top.volume / 1000, 1), "watertight": bool(top.is_watertight)},
    "screws": {"through_pcb_M3x8": len(mounts), "palm_M3x6": len(palm_screws), "inserts_M3": len(all_screws)},
    "pcb_support_posts": len(supports),
    "problems": problems,
}
(FAB / "case-report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
if problems:
    sys.exit(1)
