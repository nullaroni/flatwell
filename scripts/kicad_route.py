"""KiCad side of `npm run route`. Runs under KiCad's bundled Python (needs pcbnew).

  export-dsn <board.kicad_pcb> <board.dsn>                     board -> Freerouting
  import-ses <board.kicad_pcb> <board.ses> <routed.kicad_pcb>  Freerouting -> board

Traces are 0.25 mm, but Freerouting necks them down to ~0.19 mm to pass between
pads, so the routed board's minimum track width is set to 0.15 mm. PCBWay's
standard process goes down to 0.1 mm.
"""
import sys

import pcbnew


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "export-dsn" and len(args) == 2:
        board = pcbnew.LoadBoard(args[0])
        if not pcbnew.ExportSpecctraDSN(board, args[1]):
            sys.exit("DSN export failed")
    elif cmd == "import-ses" and len(args) == 3:
        board = pcbnew.LoadBoard(args[0])
        if not pcbnew.ImportSpecctraSES(board, args[1]):
            sys.exit("SES import failed")
        board.GetDesignSettings().m_TrackMinWidth = pcbnew.FromMM(0.15)
        pcbnew.SaveBoard(args[2], board)
    else:
        sys.exit(__doc__)


main()
