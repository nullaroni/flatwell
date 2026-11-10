"""Makes a 1:1 print sheet of the PCB's back side: <bottom.svg> -> <print.html>.

The SVG is KiCad's mirrored bottom view (what you see with the board flipped
over). It is split across two Letter landscape pages with a 20 mm overlap.
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
svg = open(src).read()
svg = re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>", "", svg)
w = float(re.search(r'width="([\d.]+)mm"', svg).group(1))
h = float(re.search(r'height="([\d.]+)mm"', svg).group(1))
inner = svg[svg.index(">", svg.index("<svg")) + 1 : svg.rindex("</svg>")]

OVERLAP, PAD = 20, 14
half = w / 2
pages = [("left part", 0, half + OVERLAP / 2), ("right part", half - OVERLAP / 2, w)]
sheets = []
for name, x0, x1 in pages:
    bar_x = x0 + 5
    bar = "".join(
        f'<line x1="{bar_x + t}" y1="{h + 6}" x2="{bar_x + t}" y2="{h + (3 if t % 50 == 0 else 4.5)}"/>'
        for t in range(0, 51, 10)
    )
    sheets.append(f"""<section class="sheet">
<div class="cap">Flatwell PCB, back side, {name}. Print at 100% (no "fit to page"), then measure the 50 mm bar.</div>
<svg xmlns="http://www.w3.org/2000/svg" width="{x1 - x0:.2f}mm" height="{h + PAD:.2f}mm" viewBox="{x0:.2f} 0 {x1 - x0:.2f} {h + PAD:.2f}">
{inner}
<g class="scale"><line x1="{bar_x}" y1="{h + 6}" x2="{bar_x + 50}" y2="{h + 6}"/>{bar}
<text x="{bar_x + 54}" y="{h + 7}">50 mm</text></g>
<line class="join" x1="{half:.2f}" y1="0" x2="{half:.2f}" y2="{h + PAD:.2f}"/>
</svg></section>""")

open(dst, "w").write(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Flatwell PCB print check</title>
<style>
  @page {{ size: letter landscape; margin: 8mm }}
  body {{ margin:0; background:#fff; color:#111; font:10pt -apple-system, system-ui, sans-serif }}
  .sheet {{ break-after:page }} .sheet:last-child {{ break-after:auto }}
  .cap {{ margin:0 0 2mm; color:#444 }}
  ol {{ margin:0 0 4mm 5mm; padding:0; max-width:240mm }} li {{ margin:0 0 1mm }}
  svg {{ display:block; overflow:hidden }}
  .scale line {{ stroke:#000; stroke-width:.3 }} .scale text {{ font-size:3.5px; fill:#000 }}
  .join {{ stroke:#c00; stroke-width:.25; stroke-dasharray:2 1.5 }}
  @media screen {{ body {{ padding:16px }} .sheet {{ margin-bottom:24px }} }}
</style></head><body>
<ol>
  <li>This is the <b>back</b> of the board, as you'd see it flipped over. Tape the two pages together at the red line.</li>
  <li><b>nice!nano:</b> lay it on the outline near the top center, chips facing you, USB port at the board edge. All 24 edge pins must sit on pads.</li>
  <li><b>Switch + socket:</b> the two large holes are for a Choc switch's pins (pushed in from the other side). A Kailh Choc hotswap socket should cover both holes and land on the two square pads.</li>
  <li><b>Diode:</b> a SOD-123 diode should span the small pad pair under each switch.</li>
</ol>
{''.join(sheets)}
</body></html>
""")
