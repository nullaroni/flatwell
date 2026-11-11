"""Builds the two case shells for 3D printing.

  npm run case          one-piece shells for PCBWay (MJF nylon):
                        fab/<variant>/flatwell-case-{tray,top}.stl, case-report.json
  npm run case:bambu    the same case cut into four pieces that fit a 256 mm home printer
                        (Bambu Lab X1 / P1 / A1): fab/<variant>/bambu/, also zipped

  uv run --with trimesh --with shapely --with manifold3d --with numpy \\
      scripts/case.py [variant] [--bambu]

Reads output/<variant>/{points.json,case.json,flatwell.kicad_pcb}.

How it goes together (z = 0 is the desk, all mm):

  tray  floor 0-2, outer wall up to 9.6, with slots at the back for USB and the power switch. Posts hold M3 heat-set inserts. The PCB
        sits on posts with its underside at 8.0 (6 mm for sockets and the nice!nano).
        Sloped ribs carry the Magic Trackpad so its top is level.
  PCB   8.0-9.6. Only switches on top.
  top   key deck 9.6-11.8, resting on the PCB; it is also the switch plate (1.2 mm
        lip, 13.8 mm holes). The palm deck around the trackpad is 13.6 high.
  M3 screws go down through the top (and the PCB, in the key area) into the inserts.

--bambu: both shells are too wide for the plate, so each is cut in two. The tray is cut at
x = -22 and the top at x = 0, so each shell bridges the other's seam. Along each seam the
pieces hold each other level with tongues: a tongue lies on the print bed and slides under
a roof printed on the other piece. The palm rests are solid and the switch holes are 13.9 mm.
Nothing needs support material.
"""
import json
import math
import re
import sys
import zipfile
from pathlib import Path

import manifold3d
import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
FDM = "--bambu" in sys.argv
VARIANT = ARGS[0] if ARGS else "macbook"
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
SWITCH_HOLE = 13.9 if FDM else 13.8   # printed holes come out a little small
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
SWITCH_SLOT_W, SWITCH_SLOT_Z = 14.0, 5.0   # power switch slot: width, and its lower edge

# --- home printing (--bambu). Heights are multiples of a 0.2 mm layer. ---------------
BED = 256.0               # Bambu Lab X1 / P1 / A1 plate
BED_KEEP = 3.0            # stay this far from the plate edge
TRAY_SEAM, TOP_SEAM = -22.0, 0.0
SEAM_GAP = 0.1            # taken off each cut face
FIT_SIDE, FIT_TIP, FIT_Z = 0.2, 0.3, 0.4   # room beside, beyond and above a tongue
TRAY_REACH, TRAY_ROOF = 6.0, 2.0           # tray tongues are the 2 mm floor; the roof sits on a pad
TRAY_PAD = TRAY_REACH + 3.0                # half-width of that pad (it meets the trackpad ribs)
TOP_REACH, TOP_TONGUE = 5.0, 0.8           # deck tongues: 0.8 mm under a 1.0 mm roof
PLA = 1.24                # g/cm3

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
        box(u["sw_x"] - 6, u["pcb_top"] - 1, u["sw_x"] + 6, u["pcb_top"] + u["sw_tab"]),     # power switch tab
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
battery_plug, reset_button = box(-36.5, 23, -23.5, 37), box(24, 24.5, 36, 35.5)
power_switch = box(u["sw_x"] - 6, u["pcb_top"] - 6, u["sw_x"] + 6, u["pcb_top"] + 3)
under_pcb = many(
    [key_rect(k, 15.2, 8.0, dx=2.5, dy=4.85) for k in points]          # hotswap socket and its pads
    + [key_rect(k, 5.2, 2.4, dy=-5.0) for k in points]                 # diode
    + [affinity.translate(affinity.rotate(circle(dx, 0, d), k["r"], origin=(0, 0)), k["x"], k["y"])
       for k in points for dx, d in ((0, 4.6), (-5.5, 3.0), (5.5, 3.0))]  # switch post and legs
    + [mcu, battery_plug, reset_button, power_switch]
    + [circle(x, y, POST_D) for x, y in mounts]
)

# --- seams for home printing -------------------------------------------------------
_, POCKET_FRONT, _, POCKET_BACK = pocket.bounds
RIB_BACK = PALM_TOP - TP_FEET - TP_BACK      # the trackpad's resting plane at the back of the pocket...
RIB_FRONT = PALM_TOP - TP_FEET - TP_FRONT    # ...and at the front


def run(y0, y1, n, first):
    """n tongues end to end from y0 to y1, alternating between the two pieces."""
    step = (y1 - y0) / n
    return [(first * (-1) ** i, y0 + i * step, y0 + (i + 1) * step) for i in range(n)]


# A lap is (owner, y0, y1, reach, z_top). Owner -1: a tongue on the left piece that reaches
# right, from the underside of the shell up to z_top (None: the shell's full height). The right
# piece gets the matching socket, roofed over FIT_Z above the tongue. Owner +1 is the mirror.
TRAY_ROOF_TOP = FLOOR + FIT_Z + TRAY_ROOF
# In the trackpad pocket the roofs must stay under the trackpad, which sits lower toward the back.
pocket_run_end = POCKET_BACK - (TRAY_ROOF_TOP + 0.2 - RIB_BACK) / (RIB_FRONT - RIB_BACK) * (POCKET_BACK - POCKET_FRONT) - 3.0
tray_runs = [(POCKET_FRONT + 1.5, pocket_run_end, 5), (-31.5, -7.5, 2), (56.0, 80.0, 2)]
tray_laps = [(o, a, b, TRAY_REACH, FLOOR) for y0, y1, n in tray_runs for o, a, b in run(y0, y1, n, -1)]
tray_pads = [box(TRAY_SEAM - TRAY_PAD, y0 - 3.0, TRAY_SEAM + TRAY_PAD, y1 + 3.0) for y0, y1, _ in tray_runs]
top_laps = (
    [(o, a, b, TOP_REACH, DECK_BOTTOM + TOP_TONGUE) for o, a, b in ((-1, -30, -18), (1, -14, -2), (1, 36, 48), (-1, 54, 66), (1, 72, 84))]
    + [(-1, 15.0, 29.0, 6.0, None)]                                         # tab under the middle screw
    + [(-1, bx["y0"] + 1.5, bx["y0"] + 3.5, TOP_REACH, DECK_BOTTOM + 1.8)]  # front strip, below the trackpad
)
if FDM:   # keep the PCB support posts off the tray seam and its pads
    under_pcb = many([under_pcb, box(TRAY_SEAM - 1.5, bx["y0"], TRAY_SEAM + 1.5, bx["y1"])] + tray_pads)


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
    """Extrudes a shapely (multi)polygon from z0 to z1. Returns a list, so slabs add up with +."""
    polys = [g for g in getattr(shape, "geoms", [shape]) if isinstance(g, Polygon) and g.area > 1e-6]
    rings = [np.asarray(ring.coords)[:-1] for poly in polys for ring in (poly.exterior, *poly.interiors)]
    if not rings:
        return []
    # Extruded by the solid-geometry library itself: an earlier version triangulated the outline
    # separately, which left stray zero-thickness walls between holes that line up.
    return [manifold3d.CrossSection(rings, manifold3d.FillRule.EvenOdd).extrude(z1 - z0).translate((0, 0, z0))]


def union(solids):
    # 0.1 micron tolerance: anything thinner would collapse to nothing in an STL file anyway
    solid = manifold3d.Manifold.batch_boolean(solids, manifold3d.OpType.Add).set_tolerance(1e-4)
    assert solid.status() == manifold3d.Error.NoError and not solid.is_empty(), "could not build the shell"
    return solid


def write_stl(solid, path):
    """Writes the STL, reads it back and returns True if it is still the same closed solid."""
    raw = solid.to_mesh64()
    trimesh.Trimesh(vertices=np.asarray(raw.vert_properties)[:, :3], faces=np.asarray(raw.tri_verts), process=False).export(path)
    mesh = trimesh.load(path)
    again = manifold3d.Manifold(manifold3d.Mesh64(vert_properties=np.asarray(mesh.vertices, np.float64), tri_verts=np.asarray(mesh.faces, np.uint64)))
    return bool(mesh.is_watertight and again.status() == manifold3d.Error.NoError and abs(again.volume() - solid.volume()) < 5.0)


def extent(solid):
    x0, y0, z0, x1, y1, z1 = solid.bounding_box()
    return np.array([x0, y0, z0]), np.array([x1, y1, z1])


def half_plane(seam_x, side):
    return box(-1000, -1000, seam_x - SEAM_GAP, 1000) if side < 0 else box(seam_x + SEAM_GAP, -1000, 1000, 1000)


def tongue_box(seam_x, lap, grow=False):
    """Plan of a tongue; grow=True gives the socket it slides into."""
    owner, y0, y1, reach, _ = lap
    tip, side = (FIT_TIP, FIT_SIDE) if grow else (0.0, 0.0)
    root = 0.0 if grow else 1.0      # a tongue starts 1 mm inside its own piece
    x0, x1 = (seam_x - root, seam_x + reach + tip) if owner < 0 else (seam_x - reach - tip, seam_x + root)
    return box(x0, y0 - side, x1, y1 + side)


def cut(shell, seam_x, laps, z0, z1):
    """Cuts a shell at x = seam_x into [left, right], leaving the tongues and sockets."""
    pieces = []
    for side in (-1, 1):
        keep, drop = slab(half_plane(seam_x, side), z0 - 1, z1 + 1), []
        for lap in laps:
            top = z1 + 1 if lap[4] is None else lap[4]
            if lap[0] == side:
                keep += slab(tongue_box(seam_x, lap), z0 - 1, top)
            else:
                drop += slab(tongue_box(seam_x, lap, grow=True), z0 - 1, top + (0 if lap[4] is None else FIT_Z))
        piece = shell ^ union(keep)
        pieces.append(piece - union(drop) if drop else piece)
    return pieces


def plan(shape, seam_x, laps, side):
    """What one piece covers, seen from above."""
    return shape.intersection(many([half_plane(seam_x, side)] + [tongue_box(seam_x, lap) for lap in laps if lap[0] == side]))


def rib(x):
    """A wedge the trackpad rests on: low at the back, high at the front."""
    low, slope = FLOOR - 0.1, (RIB_FRONT - RIB_BACK) / (POCKET_BACK - POCKET_FRONT)
    # Both ends run 1 mm into the pocket wall, so the rib overlaps it instead of just touching.
    front, back = POCKET_FRONT - 1.0, POCKET_BACK + 1.0
    side = [(front, low), (back, low), (back, RIB_BACK - slope), (front, RIB_FRONT + slope)]
    return manifold3d.Manifold.hull_points([(x + dx, y, z) for dx in (-RIB_T / 2, RIB_T / 2) for y, z in side])


usb_slot = box(-USB_SLOT_W / 2, bx["y1"] - USB_SLOT_DEPTH, USB_SLOT_W / 2, bx["y1"] + 1)
push_hole = circle(tp["cx"], tp["cy"], 20)
reset_hole = circle(30, 30, 3)
switch_slot = box(u["sw_x"] - SWITCH_SLOT_W / 2, u["pcb_top"], u["sw_x"] + SWITCH_SLOT_W / 2, bx["y1"] + 1)
wall = case.difference(inside)
key_posts = many(circle(x, y, POST_D) for x, y in mounts)
palm_posts = many(circle(x, y, POST_D) for x, y in palm_screws)
insert_holes = many(circle(x, y, INSERT_HOLE) for x, y in all_screws)

tray = union(
    slab(case.difference(many([usb_slot, push_hole, reset_hole])), 0, FLOOR)
    + slab(wall.difference(usb_slot), FLOOR, SWITCH_SLOT_Z)
    + slab(wall.difference(many([usb_slot, switch_slot])), SWITCH_SLOT_Z, PCB_BOTTOM)
    + slab(wall.difference(switch_slot), PCB_BOTTOM, DECK_BOTTOM)
    + slab(key_posts.difference(insert_holes), FLOOR, PCB_BOTTOM)
    + slab(palm_posts, FLOOR, DECK_BOTTOM - INSERT_DEPTH)
    + slab(palm_posts.difference(insert_holes), DECK_BOTTOM - INSERT_DEPTH, DECK_BOTTOM)
    + slab(many(circle(x, y, SUPPORT_D) for x, y in supports), FLOOR, PCB_BOTTOM)
    + slab(pocket_ring, FLOOR, PCB_BOTTOM)
    + slab(pocket_ring.difference(pcb.buffer(0.6)), PCB_BOTTOM, DECK_BOTTOM)
    + [rib(s * x) for s in (-1, 1) for x in RIB_X]
    + (slab(many(tray_pads), FLOOR, TRAY_ROOF_TOP) if FDM else [])
)

palm_solid = palm.difference(pocket)
# MJF: hollow palm rests. Home printing: left solid, the slicer's infill does the same job
# and the shell prints flat on its underside without support.
cavity = Polygon() if FDM else palm.buffer(-3.0).difference(many([pocket.buffer(6.0)] + [circle(x, y, 10) for x, y in palm_screws]))
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
size = np.round(np.maximum(extent(tray)[1], extent(top)[1]) - np.minimum(extent(tray)[0], extent(top)[0]), 2)
if size[0] > u["bag_w"] or size[1] > u["bag_h"]:
    problems.append(f"case is {size[0]} x {size[1]} mm, over the {u['bag_w']} x {u['bag_h']} limit")

common = {
    "screws": {"through_pcb_M3x8": len(mounts), "palm_M3x6": len(palm_screws), "inserts_M3": len(all_screws)},
    "pcb_support_posts": len(supports),
}
size_mm = {"width": size[0], "depth": size[1], "height_without_keys": size[2], "keycap_top_approx": round(DECK_BOTTOM + 10.5, 1)}

if not FDM:
    out = FAB
    out.mkdir(parents=True, exist_ok=True)
    # STL in print orientation: x right, y back, z up; each shell flat on its largest face.
    sound = {
        "tray": write_stl(tray, out / "flatwell-case-tray.stl"),
        "top": write_stl(top.translate((0, 0, -DECK_BOTTOM)), out / "flatwell-case-top.stl"),
    }
    problems += [f"{name} shell is not one closed solid" for name, ok in sound.items() if not ok or len(locals()[name].decompose()) != 1]
    report = {
        "size_mm": size_mm,
        "tray": {"volume_cm3": round(tray.volume() / 1000, 1), "watertight": sound["tray"]},
        "top": {"volume_cm3": round(top.volume() / 1000, 1), "watertight": sound["top"]},
        **common,
        "problems": problems,
    }
else:
    out = FAB / "bambu"
    out.mkdir(parents=True, exist_ok=True)

    # The seams must miss everything that stands on the tray or hangs from the PCB.
    low_parts = many([mcu, battery_plug, reset_button, power_switch]).buffer(1.0)
    if any(pad.intersects(low_parts) for pad in tray_pads):
        problems.append("a tray seam pad is under a part that hangs low from the PCB")
    for posts, d in ((mounts + palm_screws, POST_D), (supports, SUPPORT_D)):
        for x, y in posts:
            if abs(x - TRAY_SEAM) < d / 2 + 1.0 or any(pad.distance(Point(x, y)) < d / 2 + 0.5 for pad in tray_pads):
                problems.append(f"post at ({x}, {y}) is on the tray seam")
    full = {
        side: many([half_plane(TOP_SEAM, side)] + [tongue_box(TOP_SEAM, lap) for lap in top_laps if lap[0] == side and lap[4] is None])
        for side in (-1, 1)
    }
    sockets = many(tongue_box(TOP_SEAM, lap, grow=True) for lap in top_laps)
    if switch_reliefs.distance(sockets) < 1.5:
        problems.append("a top seam tongue is too close to a switch hole")
    for x, y in all_screws:
        head = circle(x, y, SCREW_HEAD)
        if not any(full[side].contains(head) for side in (-1, 1)):
            problems.append(f"screw at ({x}, {y}) straddles the top seam")
        if any(tongue_box(TOP_SEAM, lap, grow=True).intersects(head) for lap in top_laps if lap[4] is not None):
            problems.append(f"screw at ({x}, {y}) goes through a top seam tongue")

    tray_l, tray_r = cut(tray, TRAY_SEAM, tray_laps, 0.0, DECK_BOTTOM)
    top_l, top_r = cut(top, TOP_SEAM, top_laps, DECK_BOTTOM, PALM_TOP)
    tray_2d = case.difference(many([usb_slot, push_hole, reset_hole]))
    tray_detail = many([wall, key_posts, palm_posts, pocket_ring] + tray_pads + [circle(x, y, SUPPORT_D) for x, y in supports]
                       + [box(s * x - RIB_T / 2, POCKET_FRONT, s * x + RIB_T / 2, POCKET_BACK) for s in (-1, 1) for x in RIB_X])
    top_2d = many([key_deck, palm_solid]).difference(many([switch_holes, screw_holes]))
    parts = [
        ("tray-left", tray_l, 0.0, plan(tray_2d, TRAY_SEAM, tray_laps, -1), tray_detail),
        ("tray-right", tray_r, 0.0, plan(tray_2d, TRAY_SEAM, tray_laps, 1), tray_detail),
        ("top-left", top_l, DECK_BOTTOM, plan(top_2d, TOP_SEAM, top_laps, -1), palm_solid),
        ("top-right", top_r, DECK_BOTTOM, plan(top_2d, TOP_SEAM, top_laps, 1), palm_solid),
    ]

    def svg_path(geom, dx, dy):
        polys = [geom] if isinstance(geom, Polygon) else [g for g in getattr(geom, "geoms", []) if isinstance(g, Polygon)]
        return " ".join("M" + " L".join(f"{x + dx:.1f},{dy - y:.1f}" for x, y in ring.coords) + "Z"
                        for poly in polys for ring in (poly.exterior, *poly.interiors))

    pieces, svg, cell, row_h = {}, [], BED + 24, BED + 62
    for i, (name, solid, z0, shape, detail) in enumerate(parts):
        low, high = extent(solid)
        ext = [round(float(v), 2) for v in high - low]
        # print orientation: underside on the plate
        sound = write_stl(solid.translate((-low[0], -low[1], -z0)), out / f"flatwell-bambu-{name}.stl")
        if not sound or len(solid.decompose()) != 1:
            problems.append(f"{name} is not one closed solid")
        if max(ext[0], ext[1]) > BED - 2 * BED_KEEP:
            problems.append(f"{name} is {ext[0]} x {ext[1]} mm, too big for a {BED:g} mm plate")
        pieces[name] = {"size_mm": ext, "volume_cm3": round(solid.volume() / 1000, 1), "watertight": sound}

        x0, y0, x1, y1 = shape.bounds
        bed_x, bed_y = 12 + (i % 2) * cell, 12 + (i // 2) * row_h
        dx, dy = bed_x + (BED - (x1 - x0)) / 2 - x0, bed_y + (BED - (y1 - y0)) / 2 + y1
        svg += [
            f'<rect x="{bed_x}" y="{bed_y}" width="{BED:g}" height="{BED:g}" rx="4" fill="#f1f3f5" stroke="#868e96"/>',
            f'<path d="{svg_path(shape, dx, dy)}" fill="#a5d8ff" stroke="#1971c2" stroke-width="0.6" fill-rule="evenodd"/>',
            f'<path d="{svg_path(shape.intersection(detail), dx, dy)}" fill="#4dabf7" fill-rule="evenodd"/>',
            f'<text x="{bed_x + BED / 2}" y="{bed_y + BED + 20}" text-anchor="middle" font-size="13" font-weight="600">{name}</text>',
            f'<text x="{bed_x + BED / 2}" y="{bed_y + BED + 37}" text-anchor="middle" font-size="11">{ext[0]:g} × {ext[1]:g} × {ext[2]:g} mm</text>',
        ]
    width, height = 2 * cell, 2 * row_h + 12
    (out / "flatwell-bambu-plates.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {height:g}" width="{width:g}" height="{height:g}" '
        f'font-family="-apple-system, Helvetica, Arial, sans-serif" fill="#212529">\n'
        f'<rect width="{width:g}" height="{height:g}" fill="#ffffff"/>\n' + "\n".join(svg) + "\n</svg>\n"
    )

    # One download with everything to print. Fixed dates, so the zip only changes when a file does.
    with zipfile.ZipFile(out / "flatwell-bambu-case.zip", "w") as bundle:
        for path in sorted(out.glob("flatwell-bambu-*.stl")) + [out / "flatwell-bambu-plates.svg"]:
            info = zipfile.ZipInfo(path.name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, path.read_bytes())

    for shell, halves, label in ((tray, (tray_l, tray_r), "tray"), (top, (top_l, top_r), "top")):
        lost = shell.volume() - sum(h.volume() for h in halves)
        if not 0 <= lost < 1500:   # mm3: only the seam gaps and the room around the tongues
            problems.append(f"cutting the {label} changed its volume by {lost:.0f} mm3")
    solid = sum(p["volume_cm3"] for p in pieces.values())
    report = {
        "printer": {"plate_mm": [BED, BED], "layer_height_mm": 0.2, "supports": False},
        "size_mm": size_mm,
        "pieces": pieces,
        "pla_grams_if_solid": round(solid * PLA),
        "seams": {"tray_x": TRAY_SEAM, "top_x": TOP_SEAM, "tray_tongues": len(tray_laps), "top_tongues": len(top_laps)},
        **common,
        "problems": problems,
    }

(out / "case-report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
if problems:
    sys.exit(1)
