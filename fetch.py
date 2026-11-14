"""02 · NISAR data — find the GUNW pairs over the site and stream only the site window out of each ~2.4 GB file.

Owner: 02 · NISAR data (Alexandru & Eric). Status: STUB (interfaces only).

    python fetch.py ocnele_mari --list           # search only: pairs per track, pair lengths
    python fetch.py ocnele_mari                  # stream every pair's window (needs EARTHDATA_TOKEN)
    python fetch.py ocnele_mari --track 094D     # one track
    python fetch.py demo --synthetic             # offline known-answer stack, same file shapes

Writes data/work/<site>/<track>/ (never committed). This is the DRAFT hand-off to 03; agree any change with them:
    meta.json            window grid: epsg, x0, y0, dx, dy, nx, ny; wavelength (m), direction, look, polarization, synthetic
    geom.npz             line-of-sight unit vectors los_e, los_n, los_u (target → sensor, ENU) on the window grid
    <ref>_<sec>.npz      one per pair (YYYYMMDD_YYYYMMDD): phase (rad, ionosphere removed, NaN = masked), coh,
                         and QA fields: iono_used, iono_std, valid_share, main_share, iono_interp
    dem.npz              elevation (m) on the window grid, for the troposphere step in stack.py
    truth.npz            (synthetic only) the true up/east rates

Known going in (CMR, 14 Nov 2026; advisor rehearsal, 12 Nov 2026):
- 22 pairs over Ocnele Mari: 129A (13 pairs, 7 Nov 2025 → 21 Oct 2026, nothing 18 Jan → 23 Jun 2026) and 094D (9 pairs,
  20 Jun → 18 Oct 2026). Collections NISAR_L2_GUNW_BETA_V1 + NISAR_L2_GUNW_PROVISIONAL_V1; keep the newest processing.
- HTTP range reads work: ~58 MB per pair for a 50 km window, ~30 min for all 22 with 6 workers on a home line.
- `mask` is a 32-bit bitfield (spec 1.4) but older pairs store a uint8 code. Bits 0–7 water/subswath code, 8–23 anomaly
  flags, bit 24 "ionosphere interpolated" (phase still good). Decode with `mk & 0xFF`, never `mk // 100`; a naive decode
  dropped 98 % of the 094D window.
- `ionospherePhaseScreen` ships in the product but is NOT applied: subtract it.
- Keep the largest connected component only; others can be off by 2π (12 cm of line of sight).
- Products are beta/provisional ("not intended for scientific research").
"""
from __future__ import annotations

import argparse
import os
import sys

import common as C

GUNW_GRID = "science/LSAR/GUNW/grids/frequencyA/unwrappedInterferogram"   # DRAFT: verify against the product spec
RADAR_GRID = "science/LSAR/GUNW/metadata/radarGrid"
COLLECTIONS = ["NISAR_L2_GUNW_BETA_V1", "NISAR_L2_GUNW_PROVISIONAL_V1", "NISAR_L2_GUNW_V1"]


def search(site: str) -> dict:
    """ASF/CMR search over the site → {(track, ref, sec): (file_id, url)}, newest processing of each pair wins.

    Track as '129A' / '094D', dates as 'YYYYMMDD'. Searching needs no login.
    """
    raise C.todo("02", "search ASF (asf_search or earthaccess) for GUNW pairs over the site since C.NISAR_START")


def read_pair(site: str, track: str, ref: str, sec: str, url: str, token: str) -> int:
    """Stream the window of one pair over HTTP range requests and write <ref>_<sec>.npz. Returns bytes read.

    The first pair of a track fixes the window grid (meta.json, snapped to the product's 80 m lattice) and writes
    geom.npz; later pairs must land on the same grid (stop if ASF reprocessed onto another one).
    """
    raise C.todo("02", "range-read unwrappedPhase, ionospherePhaseScreen, coherenceMagnitude, connectedComponents, mask")


def write_geometry(h5, meta: dict, tdir) -> None:
    """LOS unit vectors (target → sensor, ENU) from the radarGrid cube at the site's height → geom.npz."""
    raise C.todo("02", "interpolate losUnitVectorX/Y from the radarGrid cube; los_u = sqrt(1 - e² - n²)")


def write_dem(tdir) -> None:
    """Copernicus GLO-30 DEM (open, AWS) averaged onto the window grid → dem.npz."""
    raise C.todo("02", "reproject Copernicus GLO-30 tiles onto the window grid")


def synthetic(site: str, seed: int = 7) -> None:
    """Offline known-answer stack in exactly the real file shapes: truth.npz + per-track meta/geom/pairs.

    Use the real date pattern (including the January–June gap) so the gap handling is tested too.
    """
    raise C.todo("02", "write a synthetic stack with known up/east, atmosphere, ionosphere and a planted gap")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    ap.add_argument("--list", action="store_true", help="search only")
    ap.add_argument("--synthetic", action="store_true", help="offline known-answer stack")
    ap.add_argument("--track", help="only this track, e.g. 129A")
    ap.add_argument("--workers", type=int, default=6, help="parallel streams (tune on the venue Wi-Fi)")
    a = ap.parse_args()
    if a.synthetic or C.SITES[a.site].get("synthetic"):
        return synthetic(a.site)
    pairs = search(a.site)
    if a.track:
        pairs = {k: v for k, v in pairs.items() if k[0] == a.track}
    print(f"{len(pairs)} GUNW pairs on tracks {sorted({k[0] for k in pairs})}")
    if a.list:
        return
    token = os.environ.get("EARTHDATA_TOKEN") or sys.exit("Set EARTHDATA_TOKEN (urs.earthdata.nasa.gov → Generate Token)")
    for (track, ref, sec), (_fid, url) in pairs.items():   # TODO(02): first pair per track alone, then a thread pool
        read_pair(a.site, track, ref, sec, url, token)
    for track in sorted({k[0] for k in pairs}):
        write_dem(C.site_dir(a.site, track))


if __name__ == "__main__":
    C.run_cli(main)
