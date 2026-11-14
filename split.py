"""03 · InSAR analyst: ascending + descending calibrated rates → vertical and east–west.

Owner: 03 · InSAR analyst (Alexandru & Eric). Status: STUB (interfaces only).

    python split.py ocnele_mari

Reads per track: meta.json, geom.npz (fetch.py), ts.npz (stack.py), cal.npz (calibrate.py).
Writes data/work/<site>/up_east.npz (DRAFT hand-off to 05 and 06): up, east, sig_up, sig_east (mm/yr) on the reference
track's grid, ref_track, note.

Per pixel solve [e_asc u_asc; e_desc u_desc] · [east; up] = [v_asc; v_desc].
- North is dropped: both looks are nearly blind to it (|n| ≈ 0.1); say so on the page.
- 129A and 094D cover different months (129A: Nov 2025 → Oct 2026 with a gap; 094D: Jun → Oct 2026 only). Combining
  their rates mixes windows: decide (O-05/O-01) whether to split on the common Jun–Oct 2026 window only, and say which.
- With one track only: up = LOS / u (assumes no horizontal motion) and the note must say so.
- Propagate σ through the 2×2 inverse; it stays a lower bound.
"""
from __future__ import annotations

import argparse

import common as C


def resample(src_meta: dict, arr, dst_meta: dict):
    """Nearest-neighbour sample of a src-grid array at the dst grid's pixel centres (different UTM zones allowed)."""
    raise C.todo("03", "resample one track's grid onto the reference track's grid")


def solve_up_east(v_asc, e_asc, u_asc, s_asc, v_desc, e_desc, u_desc, s_desc):
    """2×2 solve per pixel → up, east, sig_up, sig_east."""
    raise C.todo("03", "solve the 2×2 system per pixel and propagate σ")


def run(site: str) -> None:
    trs = C.tracks(site)
    if not trs:
        raise C.todo("02", f"no tracks under data/work/{site}/: run fetch.py first")
    raise C.todo("03", f"load cal.npz/geom.npz/ts.npz for {trs}, solve, write data/work/{site}/up_east.npz")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    run(ap.parse_args().site)


if __name__ == "__main__":
    C.run_cli(main)
