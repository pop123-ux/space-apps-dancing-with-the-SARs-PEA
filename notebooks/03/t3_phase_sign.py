# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Exploration only (never imported). T3, the phase sign (prompts/early-tests.md), plus one independent cross-check.

    python notebooks/03/t3_phase_sign.py ocnele_mari

T3 as predeclared: the zone-median LOS rate on 129A and on 094D, from stack.py's ts.npz (the first rate map, terrain-
relative, before the tie). Passes if both are below -2 mm/yr. Never flip the sign to pass.

Cross-check (added 14 Nov 2026, reported, not a pass rule): over the Sentinel-1 window (16.4 km), the pixel correlation
between NISAR's summer LOS rate (dates in split.SUMMER) and Sentinel-1's July to October LOS rate on the same-direction
track (129A with 029A, 094D with 007D). Both looks see vertical motion with the same sign and similar weight (u about
0.75 and 0.8), so a spatial pattern shared by both should correlate positively if the sign is right. Horizontal motion
enters with opposite signs (NISAR looks left, Sentinel-1 right), so a weak correlation is not by itself a failure.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

import common as C  # noqa: E402
import export  # noqa: E402
import split  # noqa: E402

PAIRS = {"129A": "029A", "094D": "007D"}


def zone_rates(site, track):
    d = C.WORK / site / track
    meta = C.load_json(d / "meta.json")
    ts = dict(np.load(d / "ts.npz"))
    masks = export.nisar_zone_masks(C.SITES[site], meta)
    out = {}
    for z, m in masks.items():
        v = ts["vel"][m & np.isfinite(ts["vel"])]
        out[z] = dict(rate=round(float(np.median(v)), 2) if v.size else None, n=int(v.size))
    pooled = np.concatenate([ts["vel"][masks[z] & np.isfinite(ts["vel"])] for z in ("z1", "z2", "z3", "z4")])
    out["zones_pooled"] = dict(rate=round(float(np.median(pooled)), 2), n=int(pooled.size))
    return meta, ts, out


def s1_correlation(site, track, meta, ts):
    """Pixel correlation of NISAR summer rate (resampled to the S1 40 m grid) with Sentinel-1's rate."""
    z = export.load_grid(PAIRS[track])
    rate_s1 = z["rate_mm_yr"]
    xmin, ymin, xmax, ymax = z["bounds_utm"]
    ny, nx = rate_s1.shape
    s1_meta = dict(epsg=32635, x0=xmin + (xmax - xmin) / nx / 2, y0=ymax - (ymax - ymin) / ny / 2,
                   dx=(xmax - xmin) / nx, dy=-(ymax - ymin) / ny, nx=nx, ny=ny)
    cal = C.WORK / site / track / "cal.npz"
    cum = dict(np.load(cal))["cum_cal"] if cal.exists() else ts["cum"]
    rate_n, _, used = split.summer_rate([str(x) for x in ts["dates"]], cum)
    rn = split.resample(meta, rate_n, s1_meta)
    ok = np.isfinite(rn) & np.isfinite(rate_s1)
    r = float(np.corrcoef(rn[ok], rate_s1[ok])[0, 1])
    # robust version: Spearman rank correlation
    rank = lambda a: np.argsort(np.argsort(a)).astype(float)
    rho = float(np.corrcoef(rank(rn[ok]), rank(rate_s1[ok]))[0, 1])
    return dict(s1_track=PAIRS[track], pixels=int(ok.sum()), pearson=round(r, 3), spearman=round(rho, 3),
                nisar_dates=[used[0], used[-1]])


def main():
    site = sys.argv[1] if len(sys.argv) > 1 else "ocnele_mari"
    report = {"rule": "both tracks' zone-median LOS rate below -2 mm/yr (prompts/early-tests.md, T3)", "tracks": {}}
    for track in ("129A", "094D"):
        if not (C.WORK / site / track / "ts.npz").exists():
            continue
        meta, ts, zr = zone_rates(site, track)
        report["tracks"][track] = dict(phase_sign=int(ts["phase_sign"]), zones=zr, s1=s1_correlation(site, track, meta, ts))
        print(track, json.dumps(report["tracks"][track]))
    rates = [v["zones"]["zones_pooled"]["rate"] for v in report["tracks"].values()]
    report["pass"] = len(rates) == 2 and all(r < -2 for r in rates)
    print("T3", "PASS" if report["pass"] else "NOT PASSED", rates)
    (ROOT / "notebooks" / "03" / "t3_phase_sign.json").write_text(json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()
