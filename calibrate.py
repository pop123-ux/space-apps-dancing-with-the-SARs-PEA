"""04 · Geodesist: tie each track to the GNSS velocity model, the way EGMS calibrates its own product.

Owner: 04 · Geodesist (Matei). Status: STUB (interfaces only).

    python calibrate.py ocnele_mari
    python calibrate.py ocnele_mari --model egms     # second model, once its CSV exists (model swap)

Reads per track: meta.json, geom.npz (fetch.py), ts.npz (stack.py); refs/ (refs.py).
Writes per track data/work/<site>/<track>/cal.npz (vel_cal, cum_cal, model_los, tie mask) and
products/<site>/calib.json (file contracts in docs/build-spec.md):
    {"model": "...", "tracks": [{track, direction, method: offset|plane, offset_mm_yr, slope_east_mm_yr_per_10km,
     slope_north_mm_yr_per_10km, n_tie_pixels, residual_std_mm_yr, residual_mad_mm_yr, model_los_mean_mm_yr,
     swap_delta_mm_yr}]}

The tie (DRAFT, from the advisor kit):
- NISAR − model(LOS) on pixels that are coherent (≥ C.TIE_MIN_COH), outside the salt zones + C.EXCLUDE_KM and more than
  C.STATION_HOLDOUT_M from any station (stations are held out for validate.py).
- One offset, or a plane if it cuts the scatter by more than 10 %; 3σ outliers removed twice.
- The model is a 0.1° grid: it fixes the frame-wide level and slopes only. It says nothing about a 2 km salt bowl.
- A plane hints at residual ionosphere: compare runs with and without the ionosphere layer.
- Model swap (O-06): EuVeM2022 against the EGMS GNSS model. How far the rates move is the model's share of the error.
- Rehearsal numbers to beat: offsets −8.8 (094D) / −6.0 (129A) mm/yr, robust scatter 51 / 37 mm/yr.
"""
from __future__ import annotations

import argparse

import common as C


def model_to_los(site: str, track: str, model: str):
    """Sample the velocity model at every pixel and project (ve, vn, vu) onto the track's LOS (C.enu_to_los)."""
    raise C.todo("04", "model → line of sight on the track grid")


def tie_mask(site: str, track: str, stations: list[dict]):
    """Coherent stable pixels away from the salt zones and the stations."""
    raise C.todo("04", "build the tie mask")


def fit_tie(residual, mask):
    """Offset or plane fit with outlier rejection → coefficients, residuals, method."""
    raise C.todo("04", "fit offset / plane on NISAR − model")


def run(site: str, track: str, model: str) -> dict:
    model_to_los(site, track, model)
    raise C.todo("04", f"apply the tie, write data/work/{site}/{track}/cal.npz, return the calib.json entry")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    ap.add_argument("--model", default="euvem", choices=["euvem", "egms"], help="velocity model for the tie")
    a = ap.parse_args()
    trs = C.tracks(a.site)
    if not trs:
        raise C.todo("02", f"no tracks under data/work/{a.site}/: run fetch.py first")
    entries = [run(a.site, tr, a.model) for tr in trs]
    C.save_json(C.PRODUCTS / a.site / "calib.json", {"model": a.model, "tracks": entries})


if __name__ == "__main__":
    C.run_cli(main)
