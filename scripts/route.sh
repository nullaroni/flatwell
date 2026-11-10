#!/usr/bin/env bash
# Autoroutes the key PCB and writes the PCBWay files. Run `npm run build` first.
#
#   output/<variant>/flatwell-routed.kicad_pcb  routed board (open in KiCad)
#   output/<variant>/drc.json                   KiCad design-rule check report
#   fab/<variant>/flatwell-gerbers.zip          upload this to PCBWay
#   fab/<variant>/flatwell.kicad_pcb            copy of the routed board
#   fab/<variant>/flatwell-bom.csv              parts list for PCBWay assembly (diodes)
#   fab/<variant>/flatwell-cpl.csv              where those parts go (bottom side)
#   fab/<variant>/flatwell-{top,bottom}.svg     pictures of the board
#   fab/<variant>/flatwell-print.html           1:1 print of the back, to check parts against
#
# Needs KiCad (brew install --cask kicad), Java 21+ (brew install openjdk) and
# Freerouting in tools/freerouting/ (gh release download from freerouting/freerouting).
set -euo pipefail

VARIANT="${1:-macbook}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KICAD="${KICAD_APP:-/Applications/KiCad/KiCad.app}"
KPY="$KICAD/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
KCLI="$KICAD/Contents/MacOS/kicad-cli"
JAVA="${JAVA:-/opt/homebrew/opt/openjdk/bin/java}"
FREEROUTING="${FREEROUTING:-$ROOT/tools/freerouting/freerouting-2.5.0.jar}"
OUT="$ROOT/output/$VARIANT"
FAB="$ROOT/fab/$VARIANT"
BOARD="$OUT/flatwell.kicad_pcb"
ROUTED="$OUT/flatwell-routed.kicad_pcb"

for f in "$KPY" "$KCLI" "$JAVA" "$FREEROUTING" "$BOARD"; do
  [[ -e "$f" ]] || { echo "missing: $f" >&2; exit 1; }
done
mkdir -p "$FAB/gerbers"

echo "→ exporting $VARIANT for Freerouting"
"$KPY" "$ROOT/scripts/kicad_route.py" export-dsn "$BOARD" "$OUT/flatwell.dsn"

echo "→ autorouting (a few minutes)"
"$JAVA" -Djava.awt.headless=true -jar "$FREEROUTING" \
  -de "$OUT/flatwell.dsn" -do "$OUT/flatwell.ses" \
  --router.autorouter.max_passes=100 \
  --router.fanout.enabled=false \
  --router.copper_to_edge_clearance_um=500 \
  --gui.enabled=false \
  --usage_and_diagnostic_data.disable_analytics=true \
  --api_server.enabled=false --mcp_server.enabled=false \
  > "$OUT/freerouting.log" 2>&1 || { tail -20 "$OUT/freerouting.log" >&2; exit 1; }
[[ -s "$OUT/flatwell.ses" ]] || { echo "Freerouting wrote no routes; see $OUT/freerouting.log" >&2; exit 1; }

echo "→ importing routes"
"$KPY" "$ROOT/scripts/kicad_route.py" import-ses "$BOARD" "$OUT/flatwell.ses" "$ROUTED"

echo "→ design-rule check"
if ! "$KCLI" pcb drc --format json --severity-error --exit-code-violations -o "$OUT/drc.json" "$ROUTED" > /dev/null; then
  echo "DRC found errors; see $OUT/drc.json" >&2
  DRC_FAILED=1
fi

echo "→ fab files"
rm -f "$FAB"/gerbers/*
"$KCLI" pcb export gerbers -o "$FAB/gerbers/" \
  --layers F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
  "$ROUTED" > /dev/null
"$KCLI" pcb export drill -o "$FAB/gerbers/" "$ROUTED" > /dev/null
(cd "$FAB/gerbers" && rm -f ../flatwell-gerbers.zip && zip -q ../flatwell-gerbers.zip ./*)
"$KCLI" pcb export pos --side back --format csv --units mm --smd-only -o "$FAB/flatwell-cpl.csv" "$ROUTED" > /dev/null
"$KPY" - "$FAB/flatwell-cpl.csv" "$FAB/flatwell-bom.csv" <<'PY'
import csv, sys
from collections import defaultdict
parts = defaultdict(list)
with open(sys.argv[1]) as f:
    for row in csv.DictReader(f):
        parts[(row["Val"], row["Package"])].append(row["Ref"])
with open(sys.argv[2], "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Quantity", "Value", "Package", "Manufacturer Part Number"])
    for (val, pkg), refs in sorted(parts.items()):
        mpn = "1N4148W-7-F" if val == "1N4148W" else ""
        w.writerow([" ".join(sorted(refs, key=lambda r: (len(r), r))), len(refs), val, pkg, mpn])
PY
"$KCLI" pcb export svg -o "$FAB/flatwell-top.svg" --layers F.Cu,F.Silkscreen,Edge.Cuts \
  --mode-single --page-size-mode 2 --exclude-drawing-sheet "$ROUTED" > /dev/null
"$KCLI" pcb export svg -o "$FAB/flatwell-bottom.svg" --layers B.Cu,B.Silkscreen,Edge.Cuts \
  --mode-single --page-size-mode 2 --exclude-drawing-sheet --mirror "$ROUTED" > /dev/null

"$KPY" "$ROOT/scripts/pcb_print.py" "$FAB/flatwell-bottom.svg" "$FAB/flatwell-print.html"

cp "$ROUTED" "$FAB/flatwell.kicad_pcb"

echo "✓ routed board: $ROUTED"
echo "✓ PCBWay files: $FAB/flatwell-gerbers.zip (+ flatwell-bom.csv, flatwell-cpl.csv for assembly)"
[[ -z "${DRC_FAILED:-}" ]] || exit 1
