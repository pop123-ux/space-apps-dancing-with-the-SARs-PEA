# Owner: 04 · Geodesist (Matei)
"""Exploration only (never imported). Is NASA's ionosphere layer what makes 094D's salt zones look like uplift?

    python notebooks/04/iono_ablation_094d.py         (Earthdata token from .env; about 15 MB per pair, cached)

Why: 094D fails the sign test with NASA's interferograms, ionosphere subtracted (zones +23.5 mm/yr), but 02's own
pairs from the single-look data, with no ionosphere layer, give +3.5 mm/yr (DECISIONS.md, 15 Nov 05:30). 094D is an
evening pass (17:28 UTC), when the ionosphere is far more active than at 129A's 03:20 UTC, and L-band feels it about
16 times more than Sentinel-1's C-band. So: the same stack twice, on the same pixels.
  A  phase as stored in data/work/ocnele_mari/094D/ (NASA ionosphere layer subtracted, the team's default)
  B  the same with the layer added back (no ionosphere correction)
Stack = 04's stand-in (data/work/ocnele_mari/r04/r04_129a.py): elevation slope per pair, stable-ground reference,
small-baseline inversion, one rate per group. Reported per variant: the four zones, alone and minus a 1 to 3 km ring,
and the robust scatter of the rate on stable ground.
Writes notebooks/04/iono_ablation_094d.json. Caches the layer in data/work/ocnele_mari/r04/iono094D/ (git-ignored).
"""
import csv
import io
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R04 = ROOT / "data" / "work" / "ocnele_mari" / "r04"
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(R04))
import numpy as np  # noqa: E402

import common as C  # noqa: E402
import r04_129a as R  # noqa: E402

TR = "094D"
SRC = ROOT / "data" / "work" / "ocnele_mari" / TR
G = "science/LSAR/GUNW/grids/frequencyA/unwrappedInterferogram"


def iono_layer(url, meta, key):
    out = R04 / "iono094D" / f"{key}.npy"
    if out.exists():
        return np.load(out)
    import h5py
    out.parent.mkdir(parents=True, exist_ok=True)
    f = R.RangeFile(url, R.token())
    with h5py.File(io.BufferedReader(f, 1 << 20), "r") as h:
        g = h[G]; pol = h["science/LSAR/GUNW/grids/frequencyA/listOfPolarizations"][0].decode()
        x, y = g["xCoordinates"][:], g["yCoordinates"][:]
        ri = R.idx(y, meta["y0"], meta["ny"], meta["dy"]); ci = R.idx(x, meta["x0"], meta["nx"], meta["dx"])
        ion = R.take(g[f"{pol}/ionospherePhaseScreen"], ri, ci, np.nan).astype(np.float32)
    np.save(out, ion); print(f"  {key}: ionosphere layer {f.nbytes / 1e6:.0f} MB", flush=True)
    return ion


def ring_stats(meta, vel):
    X, Y = R.grid_xy(meta); res = {}
    for z in C.SITES["ocnele_mari"]["zones"]:
        zx, zy = C.to_xy(meta["epsg"], z["lon"], z["lat"]); d = np.hypot(X - zx, Y - zy)
        inz, ring = d <= z["r_m"], (d >= 1000) & (d <= 3000)
        a, r = np.nanmedian(vel[inz]), np.nanmedian(vel[ring])
        res[z["id"]] = dict(zone=round(float(a), 1), zone_minus_ring=round(float(a - r), 1))
    st = ~R.zone_mask(meta, C.EXCLUDE_KM * 1000); v = vel[st & np.isfinite(vel)]
    res["stable_scatter"] = round(float(1.4826 * np.median(abs(v - np.median(v)))), 1)
    res["all_zones"] = round(float(np.nanmedian(vel[R.zone_mask(meta, 0)])), 1)
    return res


def main():
    meta = C.load_json(SRC / "meta.json")
    cat = {f"{r['ref_date'].replace('-', '')}_{r['sec_date'].replace('-', '')}": r["url"].strip()
           for r in csv.DictReader(open(ROOT / "data" / "scenes" / "ocnele_mari_gunw.csv", encoding="utf-8")) if r["track"] == TR}
    pairs = sorted(p.stem for p in SRC.glob("2*_2*.npz"))
    iono = {k: iono_layer(cat[k], meta, k) for k in pairs}
    dz = np.load(SRC / "dem.npz"); dem = dz["dem"] if "dem" in dz.files else dz["height"]
    out = {"track": TR, "pairs": len(pairs), "iono_rad_std_per_pair": {k: round(float(np.nanstd(v)), 2) for k, v in iono.items()}}
    for name, add in (("A_iono_subtracted", False), ("B_no_iono", True)):
        d = R04 / f"abl094D_{name}"; shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
        C.save_json(d / "meta.json", {**meta, "site": "ocnele_mari", "track": TR})
        np.savez_compressed(d / "dem.npz", height=dem)
        for k in pairs:
            z = np.load(SRC / f"{k}.npz"); ph = z["phase"].astype(np.float32)
            if add:
                ph = np.where(np.isfinite(ph) & np.isfinite(iono[k]), ph + iono[k], np.nan).astype(np.float32)
            else:   # the same pixels in both variants
                ph = np.where(np.isfinite(iono[k]), ph, np.nan).astype(np.float32)
            np.savez_compressed(d / f"{k}.npz", phase=ph, coh=z["coh"], iono_used=not add)
        R.TDIR = d; R.TRACK = TR
        R.stack()
        ts = np.load(d / "ts.npz", allow_pickle=True)
        out[name] = ring_stats(meta, ts["vel"])
        print(name, json.dumps(out[name]), flush=True)
    Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
