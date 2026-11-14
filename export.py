"""06 · App developer: turn the numbers into what the page reads: products/<site>/.

Owner: 06 · App developer (Darius). Status: STUB (interfaces only). Until it works, build the page on
`python mock_products.py` (products/mock/), which writes the same contract with invented values.

    python export.py ocnele_mari

Reads: up_east.npz (split.py), per track meta.json/ts.npz/cal.npz, products/<site>/stations.geojson + checks.json
(validate.py) and calib.json (calibrate.py).
Writes products/<site>/ (file contracts in docs/build-spec.md): manifest.json, up.png, east.png, los_<track>.png,
frames/<track>/<date>.png, series.json, up.tif, east.tif, and updates products/index.json.

Starting points (advisor kit + D-002):
- Leaflet image overlays are axis-aligned: resample UTM grids to a lon/lat grid (~100 m) for the PNGs; the GeoTIFFs keep
  the original grid.
- Colours RdBu diverging, red = sinking / away; a fixed, symmetric, readable scale per layer and per track for frames.
- manifest.view carries D-002: open on Ocnele Mari (center/zoom); Romania is context only.
- Honest slider: no frames invented across the 18 Jan → 23 Jun 2026 gap; manifest frames carry the gaps so the page
  can label "no data".
- Grey out pixels whose |rate| < 2σ (decision with 03).
- manifest.synthetic must be true for demo/mock; the page shows "simulated, not data" whenever it is.
"""
from __future__ import annotations

import argparse

import common as C


def lonlat_grid(meta: dict, step_deg: float = 0.0012):
    """Regular lon/lat grid inside the (rotated) UTM window → (LON, LAT), bounds [[S, W], [N, E]]."""
    raise C.todo("06", "lon/lat display grid for the overlays")


def overlay_png(arr, path, vmax: float) -> None:
    """RdBu PNG with transparency where there is no data (or where |rate| < 2σ)."""
    raise C.todo("06", "write one overlay PNG")


def export_layers(site: str) -> list[dict]:
    raise C.todo("06", "up/east/LOS rate overlays → manifest.layers")


def export_frames(site: str) -> dict:
    raise C.todo("06", "cumulative frames per track and date → manifest.frames (with gaps)")


def export_series(site: str) -> list[dict]:
    raise C.todo("06", "series at the salt zones and stations → series.json")


def write_manifest(site: str, layers: list[dict], frames: dict) -> None:
    raise C.todo("06", "manifest.json incl. view (D-002), synthetic flag, checks summary, credits")


def write_tifs(site: str) -> None:
    raise C.todo("06", "up.tif / east.tif on the original grid (rasterio)")


def run(site: str) -> None:
    layers = export_layers(site)
    frames = export_frames(site)
    export_series(site)
    write_manifest(site, layers, frames)
    write_tifs(site)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    run(ap.parse_args().site)


if __name__ == "__main__":
    C.run_cli(main)
