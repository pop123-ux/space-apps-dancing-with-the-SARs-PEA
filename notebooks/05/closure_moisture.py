# Owner: 05 · Validator (Paul)
# Exploration only (never imported). Needs the 58 HyP3 ZIPs (python sentinel1/scripts/download.py) and
# data/work/ocnele_mari/sm/sm_zones.csv (notebooks/05/soil_moisture.py). Run from the repo root:
#   python notebooks/05/closure_moisture.py
# Writes notebooks/05/closure_moisture.csv and .json (small derived tables) and docs/figures/05_closure_vs_moisture.png.
"""Does Sentinel-1 phase closure follow soil-moisture change? (05 red-team idea 2, 14 Nov 2026)

Closure of a triangle of dates i < j < k is d_ij + d_jk - d_ik per pixel (mm, LOS), computed exactly as
sentinel1/scripts/fit.py does for its baseline quality numbers: coherence >= 0.35, connected component > 0, not
water, the main connected component of the reference band, each pair zeroed on the 3 to 6.5 km reference-band median.
Ground motion cancels in a closed triangle; what is left is noise, unwrapping errors and processes such as soil
moisture that change the phase without moving the ground.

Predeclared test (written before any closure was computed): for each triangle and area, the median absolute closure
against the moisture range across the triangle's three dates (max minus min, NISAR SME2 recommended retrievals, the
area's own moisture where it has support, else the whole window), Spearman rho, both tracks pooled and per track.
"""
from __future__ import annotations

import csv
import json
import pathlib
import re
import sys
import zipfile

import numpy as np
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "sentinel1" / "scripts"))
import common as C  # noqa: E402
from fit import FACTOR, STEP, SUFFIXES, geometry  # noqa: E402  (03's code, read only)

RAW = ROOT / "sentinel1" / "raw"
SM = C.WORK / "ocnele_mari" / "sm"
HERE = pathlib.Path(__file__).resolve().parent
MAX_DAYS = 2


def read_product(p: pathlib.Path, bounds):
    """fit.read_product with rasterio instead of the osgeo bindings: same grid, nearest neighbour, NaN outside."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.vrt import WarpedVRT
    from rasterio.transform import from_origin
    names = zipfile.ZipFile(p).namelist()
    n = int(round((bounds[2] - bounds[0]) / STEP))
    out = {}
    for key, suffix in SUFFIXES.items():
        if key not in ("phase", "coh", "comp", "water"):
            continue
        name = next(x for x in names if x.endswith("_" + suffix + ".tif"))
        with rasterio.open(f"zip://{p.resolve()}!/{name}") as src, WarpedVRT(
                src, crs="EPSG:32635", transform=from_origin(bounds[0], bounds[3], STEP, STEP), width=n, height=n,
                resampling=Resampling.nearest, nodata=np.nan, dtype="float32") as v:
            out[key] = v.read(1)
    return out


def moisture():
    """date -> {area: moisture} from the recommended retrievals, areas with at least 3 pixels."""
    with open(SM / "sm_zones.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for r in rows:
        d = {}
        for a in ("z1", "z2", "z3", "z4", "ref_band", "control", "window"):
            if r.get(f"{a}_sm") and int(r.get(f"{a}_n") or 0) >= 3:
                d[a] = float(r[f"{a}_sm"])
        out[r["date"]] = d
    return out


def nearest(sm, d):
    day = np.datetime64(d)
    best = min(sm, key=lambda x: abs((np.datetime64(x) - day).astype(int)))
    return sm[best] if abs((np.datetime64(best) - day).astype(int)) <= MAX_DAYS else None


def main():
    geo = geometry()
    areas = {f"z{i}": m for i, m in enumerate(geo["masks"], start=1)}
    areas.update(ref_band=geo["refs"][0], control=geo["control"], window=np.ones_like(geo["control"], bool))
    sm = moisture()
    rows = []
    for track in ("029A", "007D"):
        files = sorted(RAW.glob(f"*-{track}-*.zip"))
        pairs = [tuple(re.findall(r"20\d{6}", f.stem)) for f in files]
        index = {pq: i for i, pq in enumerate(pairs)}
        print(track, len(files), "pairs", flush=True)
        data = []
        for f in files:
            p = read_product(f, geo["bounds"])
            valid = (p["coh"] >= .35) & (p["comp"] > 0) & (p["water"] == 1) & np.isfinite(p["phase"])
            ref = geo["refs"][0] & valid
            labels, counts = np.unique(p["comp"][ref], return_counts=True)
            valid &= p["comp"] == labels[np.argmax(counts)]
            d = p["phase"] * FACTOR
            d = d - np.median(d[geo["refs"][0] & valid])
            data.append(np.where(valid, d, np.nan))
        dates = sorted({d for pq in pairs for d in pq})
        for (a, c), ac in index.items():
            for b in dates:
                if a < b < c and (a, b) in index and (b, c) in index:
                    clo = data[index[a, b]] + data[index[b, c]] - data[ac]
                    m3 = [nearest(sm, f"{x[:4]}-{x[4:6]}-{x[6:]}") for x in (a, b, c)]
                    for name, mask in areas.items():
                        v = clo[mask & np.isfinite(clo)]
                        key = name if all(m and name in m for m in m3) else "window"
                        ms = [m[key] for m in m3 if m and key in m]
                        rows.append(dict(track=track, i=a, j=b, k=c, area=name, pixels=int(v.size),
                                         closure_abs_median_mm=round(float(np.median(np.abs(v))), 3) if v.size else None,
                                         closure_median_mm=round(float(np.median(v)), 3) if v.size else None,
                                         moisture_source=key if len(ms) == 3 else None,
                                         moisture_range=round(max(ms) - min(ms), 4) if len(ms) == 3 else None))
    cols = list(rows[0])
    with open(HERE / "closure_moisture.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows({k: ("" if r[k] is None else r[k]) for k in cols} for r in rows)

    result = {}
    for area in areas:
        for track in ("029A", "007D", "both"):
            sel = [r for r in rows if r["area"] == area and (track == "both" or r["track"] == track)
                   and r["closure_abs_median_mm"] is not None and r["moisture_range"] is not None and r["pixels"] >= 5]
            if len(sel) < 6:
                result[f"{track} {area}"] = dict(n=len(sel), note="fewer than 6 triangles with closure and moisture")
                continue
            x = np.array([r["moisture_range"] for r in sel]) * 100
            y = np.array([r["closure_abs_median_mm"] for r in sel])
            rho, p = stats.spearmanr(x, y)
            result[f"{track} {area}"] = dict(n=len(sel), rho=round(float(rho), 2), p=round(float(p), 3),
                                             closure_abs_median_mm=round(float(np.median(y)), 2),
                                             moisture_range_pct=[round(float(x.min()), 1), round(float(x.max()), 1)],
                                             moisture_source=sorted({r["moisture_source"] for r in sel}))
    (HERE / "closure_moisture.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    for k, v in result.items():
        print(f"{k:16s}", v)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), constrained_layout=True)
    for ax, area in zip(axes, ("window", "control", "z1")):
        for track, mk in (("029A", "o"), ("007D", "s")):
            sel = [r for r in rows if r["area"] == area and r["track"] == track and r["closure_abs_median_mm"] is not None
                   and r["moisture_range"] is not None]
            ax.scatter([100 * r["moisture_range"] for r in sel], [r["closure_abs_median_mm"] for r in sel], marker=mk,
                       label=track)
        v = result.get(f"both {area}", {})
        ax.set_title(f"{area}: rho {v.get('rho', 'n/a')} (n {v.get('n', 0)})", fontsize=10)
        ax.set_xlabel("moisture range across the 3 dates, % points")
        ax.set_ylabel("median |closure|, mm")
        ax.legend(fontsize=8)
    fig.suptitle("Sentinel-1 triangle closure vs NISAR soil-moisture change, Jul to Oct 2026", fontsize=10)
    fig.savefig(C.DOCS / "figures" / "05_closure_vs_moisture.png", dpi=100)


if __name__ == "__main__":
    main()
