# Owner: 05 · Validator (Paul)
# Exploration only (never imported). Independent weather-model check of 03's troposphere sensitivity (T4).
#   python notebooks/05/tropo_opera.py
# Needs: the 58 HyP3 ZIPs (sentinel1/scripts/download.py), EARTHDATA_TOKEN in .env with the OPERA data licence
# accepted. Caches small window cuts of OPERA in data/work/ocnele_mari/tropo/ (git-ignored). Writes
# notebooks/05/tropo_opera.json (zone results and the sign check). Predeclared in docs/validation-log.md.
"""Correct the Sentinel-1 summer stack with OPERA TROPO-ZENITH and compare zone changes with fit.py's runs.

OPERA L4 TROPO-ZENITH v1: zenith wet and hydrostatic delay (m), global 0.0703 deg grid, 145 heights, every 6 hours,
from ECMWF HRES through RAiDER. Only the HDF5 chunks that cover the Sentinel-1 window are fetched (a few MB per file
instead of 2.2 GB). Per acquisition the total zenith delay is interpolated in time (the two maps around the
acquisition start), in height (each pixel's HyP3 DEM elevation) and bilinearly in latitude and longitude, then mapped
to the line of sight by dividing by the look vector's up component sin(lv_theta).

Sign: a longer delay at the later date makes the ground look farther away, i.e. a negative LOS change under fit.py's
convention (positive towards the satellite). So the corrected pair is d_ab + 1000 * (L_b - L_a) mm, then re-zeroed on
the reference band. The script checks this on the data: the phase-elevation slope on the reference band must shrink.
"""
from __future__ import annotations

import json
import pathlib
import re
import struct
import sys
import urllib.error
import urllib.request
import warnings
import zipfile
import zlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "sentinel1" / "scripts"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import common as C  # noqa: E402
import soil_moisture as SMR  # noqa: E402  (token reader and the pyfive patch)
from fit import FACTOR, STEP, date_groups, geometry, solve, stats  # noqa: E402  (03's code, read only)

warnings.filterwarnings("ignore")
RAW = ROOT / "sentinel1" / "raw"
CACHE = C.site_dir("ocnele_mari", "tropo")
HERE = pathlib.Path(__file__).resolve().parent
MAX_HEIGHT_M = 2500
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json?short_name=OPERA_L4_TROPO-ZENITH_V1&page_size=10&temporal="
ASF = ("https://api.daac.asf.alaska.edu/services/search/param?intersectsWith=POINT(24.29%2045.088)&platform=Sentinel-1"
       "&processingLevel=SLC&start=2026-07-01T00:00:00Z&end=2026-10-10T00:00:00Z&output=json&maxResults=500")


# ------------------------------------------------------------------ acquisition times
def acquisition_times() -> dict:
    """(track, YYYYMMDD) -> UTC start time as numpy datetime64[s]."""
    with urllib.request.urlopen(ASF, timeout=120) as r:
        rows = json.load(r)[0]
    out = {}
    for g in rows:
        track = f"{int(g['track']):03d}{g['flightDirection'][0]}"
        t = np.datetime64(g["startTime"][:19], "s")
        key = (track, g["startTime"][:10].replace("-", ""))
        out[key] = min(out.get(key, t), t)
    return out


# ------------------------------------------------------------------ OPERA window reads
def opera_url(t: np.datetime64) -> str:
    stamp = str(np.datetime64(t, "s"))[:19]
    with urllib.request.urlopen(CMR + f"{stamp}Z,{stamp}Z", timeout=60) as r:
        entries = json.load(r)["feed"]["entry"]
    for e in entries:
        if e["time_start"][:19] == stamp:
            return next(lk["href"] for lk in e["links"] if lk["href"].endswith(".nc") and lk["href"].startswith("https"))
    raise LookupError(f"no OPERA TROPO granule at {stamp}")


def signed(url: str, tok: str) -> str:
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    try:
        urllib.request.build_opener(NoRedirect).open(
            urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"}), timeout=60)
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307) and e.headers.get("Location"):
            return e.headers["Location"]
        raise SystemExit(f"OPERA download refused (HTTP {e.code}): {e.read(300).decode(errors='replace')}")
    return url


def wanted_leaves(fh, address, dims, cs, sel):
    """Walk the HDF5 v1 chunk B-tree, descending only into children whose key range can hold a wanted chunk.
    Keys are chunk offsets in lexicographic (C) order; child i spans [key_i, key_{i+1})."""
    from itertools import product

    from pyfive.btree import BTreeV1RawDataChunks
    targets = sorted(tuple(t) + (0,) for t in product(*[range((s.start // c) * c, s.stop, c) for s, c in zip(sel, cs)]))
    reader = BTreeV1RawDataChunks.__new__(BTreeV1RawDataChunks)
    reader.fh, reader.dims = fh, dims
    leaves = []

    def visit(addr, level):
        node = reader._read_node(addr, level)
        keys = [tuple(k["chunk_offset"]) for k in node["keys"]]
        if node["node_level"] == 0:
            leaves.extend((k, a) for k, a in zip(node["keys"], node["addresses"]) if tuple(k["chunk_offset"]) in targets)
            return
        for i, a in enumerate(node["addresses"]):
            lo, hi = keys[i], keys[i + 1] if i + 1 < len(keys) else None
            if any(lo <= t and (hi is None or t < hi) for t in targets):
                visit(a, node["node_level"] - 1)
    visit(address, None)
    return leaves


def read_window(fh, ds, sel):
    """Read only the HDF5 chunks of a 4-D dataset (time, height, lat, lon) that touch the index ranges in sel."""
    from pyfive.btree import BTreeV1RawDataChunks
    do = ds._dataobjects
    do._get_chunk_params()
    cs = do.chunks
    out = np.full([s.stop - s.start for s in sel], np.nan, np.float32)
    for key, addr in wanted_leaves(fh, do._chunk_address, do._chunk_dims, cs, sel):
        if True:
            start = key["chunk_offset"][:-1]
            if not all(st < s.stop and st + c > s.start for st, c, s in zip(start, cs, sel)):
                continue
            fh.seek(addr)
            buf = BTreeV1RawDataChunks._filter_chunk(fh.read(key["chunk_size"]), key["filter_mask"],
                                                     do.filter_pipeline, 4)
            chunk = np.frombuffer(buf, "<f4").reshape(cs)
            src = tuple(slice(max(s.start, st) - st, min(s.stop, st + c) - st) for st, c, s in zip(start, cs, sel))
            dst = tuple(slice(max(s.start, st) - s.start, min(s.stop, st + c) - s.start) for st, c, s in zip(start, cs, sel))
            out[dst] = chunk[src]
    return out


def opera_cut(t: np.datetime64, box, tok) -> dict:
    """Total zenith delay (m) on (height, lat, lon) around the window, cached as a small npz."""
    path = CACHE / f"opera_{str(t)[:13].replace('-', '').replace('T', '_')}.npz"
    if path.exists():
        z = np.load(path)
        return {k: z[k] for k in z.files}
    import fsspec
    import pyfive
    url = signed(opera_url(t), tok)
    fs = fsspec.filesystem("http")
    with fs.open(url, "rb", block_size=2 ** 18, cache_type="blockcache") as fh:
        h = pyfive.File(fh)
        lat, lon, hgt = h["latitude"][:], h["longitude"][:], h["height"][:]
        li = np.where((lat >= box[1] - 0.15) & (lat <= box[3] + 0.15))[0]
        lo = np.where((lon >= box[0] - 0.15) & (lon <= box[2] + 0.15))[0]
        hi = np.where(hgt <= MAX_HEIGHT_M)[0]
        sel = (slice(0, 1), slice(hi.min(), hi.max() + 1), slice(li.min(), li.max() + 1), slice(lo.min(), lo.max() + 1))
        total = read_window(fh, h["wet_delay"], sel)[0] + read_window(fh, h["hydrostatic_delay"], sel)[0]
    out = dict(height=hgt[hi], lat=lat[li], lon=lon[lo], ztd=total)
    np.savez_compressed(path, **out)
    return out


def ztd_at(cut, lat, lon, elev):
    """Bilinear in lat/lon, linear in height, for arrays of pixels."""
    la, lo, hg, z = cut["lat"], cut["lon"], cut["height"], cut["ztd"]
    order = np.argsort(la)
    la, z = la[order], z[:, order, :]
    fy = np.interp(lat, la, np.arange(la.size))
    fx = np.interp(lon, lo, np.arange(lo.size))
    y0, x0 = np.clip(np.floor(fy).astype(int), 0, la.size - 2), np.clip(np.floor(fx).astype(int), 0, lo.size - 2)
    wy, wx = fy - y0, fx - x0
    col = (z[:, y0, x0] * (1 - wy) * (1 - wx) + z[:, y0 + 1, x0] * wy * (1 - wx)
           + z[:, y0, x0 + 1] * (1 - wy) * wx + z[:, y0 + 1, x0 + 1] * wy * wx)          # (height, n)
    fh = np.interp(elev, hg, np.arange(hg.size))
    h0 = np.clip(np.floor(fh).astype(int), 0, hg.size - 2)
    wh = fh - h0
    idx = np.arange(elev.size)
    return col[h0, idx] * (1 - wh) + col[h0 + 1, idx] * wh


def delay_map(t, box, tok, lat, lon, elev):
    """Zenith total delay (m) per pixel at time t, linear between the 6-hourly maps around it."""
    hours = (t - t.astype("datetime64[D]")).astype(int) / 3600
    t0 = t.astype("datetime64[D]") + np.timedelta64(int(hours // 6) * 6, "h")
    t1 = t0 + np.timedelta64(6, "h")
    w = (t - t0).astype(int) / (6 * 3600)
    a = ztd_at(opera_cut(t0, box, tok), lat, lon, elev)
    b = ztd_at(opera_cut(t1, box, tok), lat, lon, elev)
    return a * (1 - w) + b * w


# ------------------------------------------------------------------ Sentinel-1
def read_product(p, bounds, keys=("phase", "coh", "comp", "water", "dem", "theta")):
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from rasterio.vrt import WarpedVRT
    suffix = dict(phase="unw_phase", coh="corr", comp="conncomp", water="water_mask", dem="dem", theta="lv_theta")
    names = zipfile.ZipFile(p).namelist()
    n = int(round((bounds[2] - bounds[0]) / STEP))
    out = {}
    for k in keys:
        name = next(x for x in names if x.endswith("_" + suffix[k] + ".tif"))
        with rasterio.open(f"zip://{p.resolve()}!/{name}") as src, WarpedVRT(
                src, crs="EPSG:32635", transform=from_origin(bounds[0], bounds[3], STEP, STEP), width=n, height=n,
                resampling=Resampling.nearest, nodata=np.nan, dtype="float32") as v:
            out[k] = v.read(1)
    return out


def main():
    tok = SMR.token()
    SMR.patch_pyfive()
    geo = geometry()
    from pyproj import Transformer
    lon, lat = Transformer.from_crs(32635, 4326, always_xy=True).transform(geo["X"], geo["Y"])
    box = (float(lon.min()), float(lat.min()), float(lon.max()), float(lat.max()))
    times = acquisition_times()
    ref = geo["refs"][0]
    areas = [("zone_1", geo["masks"][0]), ("zone_2", geo["masks"][1]), ("zone_3", geo["masks"][2]),
             ("zone_4", geo["masks"][3]), ("outer_control", geo["control"])]
    summary = json.loads((ROOT / "sentinel1/analysis/summary.json").read_text(encoding="utf-8"))
    result = {}
    for track in ("029A", "007D"):
        files = sorted(RAW.glob(f"*-{track}-*.zip"))
        pairs = [re.findall(r"20\d{6}", f.stem) for f in files]
        dates = sorted({d for pq in pairs for d in pq})
        ix = {d: i for i, d in enumerate(dates)}
        edges = [(ix[a], ix[b]) for a, b in pairs]
        groups = date_groups(edges, len(dates))
        rows = [read_product(f, geo["bounds"]) for f in files]
        dem = rows[0]["dem"]
        up = np.sin(rows[0]["theta"])
        ok = np.isfinite(dem) & np.isfinite(up) & (up > 0.2)
        los = {}
        for d in dates:
            t = times[(track, d)]
            z = np.full(dem.shape, np.nan)
            z[ok] = delay_map(t, box, tok, lat[ok], lon[ok], dem[ok]) / up[ok]
            los[d] = z
            print(f"{track} {d} {str(t)[11:16]} UTC: LOS delay median {np.nanmedian(z):.3f} m, "
                  f"range in window {np.nanpercentile(z, 2):.3f} to {np.nanpercentile(z, 98):.3f} m", flush=True)
        t_yr = (np.array([f"{d[:4]}-{d[4:6]}-{d[6:]}" for d in dates], dtype="datetime64[D]")
                - np.datetime64(f"{dates[0][:4]}-{dates[0][4:6]}-{dates[0][6:]}")).astype(float) / 365.25
        out, check = {}, []
        for label, corr in (("baseline_reproduced", False), ("opera", True)):
            ds, ws = [], []
            for (a, b), p in zip(pairs, rows):
                valid = (p["coh"] >= .35) & (p["comp"] > 0) & (p["water"] == 1) & np.isfinite(p["phase"])
                labels, counts = np.unique(p["comp"][ref & valid], return_counts=True)
                valid &= p["comp"] == labels[np.argmax(counts)]
                d = p["phase"] * FACTOR
                if corr:
                    raw_slope = np.polyfit(dem[ref & valid & ok], (d - np.median(d[ref & valid]))[ref & valid & ok], 1)[0]
                    d = d + 1000 * (los[b] - los[a])
                    valid &= ok
                d = d - np.median(d[ref & valid])
                if corr:
                    new_slope = np.polyfit(dem[ref & valid], d[ref & valid], 1)[0]
                    check.append(dict(pair=f"{a}_{b}", slope_before_mm_per_100m=round(100 * raw_slope, 2),
                                      slope_after_mm_per_100m=round(100 * new_slope, 2)))
                ds.append(np.where(valid, d, np.nan))
                ws.append(np.where(valid, p["coh"] ** 2, 0))
            y = solve(edges, len(dates), np.stack(ds), np.stack(ws), groups)
            good = np.isfinite(y).all(axis=0)
            res = {}
            for name, mask in areas:
                keep = mask & good
                res[name] = ({"pixels": int(keep.sum()), **{k: v for k, v in stats(t_yr, np.median(y[:, keep], axis=1),
                                                                                   groups).items()
                                                            if k in ("window_fit_mm", "linear_mm_yr")}}
                             if keep.sum() else {"pixels": 0})
            out[label] = res
        shrank = sum(abs(c["slope_after_mm_per_100m"]) < abs(c["slope_before_mm_per_100m"]) for c in check)
        out["sign_check"] = dict(pairs=len(check), slope_shrank=int(shrank),
                                 median_abs_before=round(float(np.median([abs(c["slope_before_mm_per_100m"]) for c in check])), 2),
                                 median_abs_after=round(float(np.median([abs(c["slope_after_mm_per_100m"]) for c in check])), 2),
                                 per_pair=check)
        out["summary_json"] = {k: {"window_fit_mm": v.get("window_fit_mm"), "pixels": v.get("pixels")}
                               for k, v in summary[track]["fits"]["elevation_correction"].items()}
        out["summary_json_baseline"] = {k: {"window_fit_mm": v.get("window_fit_mm"), "pixels": v.get("pixels")}
                                        for k, v in summary[track]["fits"]["baseline"].items()}
        result[track] = out
        sc = out["sign_check"]
        print(f"{track} sign check: elevation slope shrank on {sc['slope_shrank']} of {sc['pairs']} pairs "
              f"(median |slope| {sc['median_abs_before']} -> {sc['median_abs_after']} mm per 100 m)")
        for name, _ in areas:
            def wf(x):
                return "n/a" if x is None or x.get("window_fit_mm") is None else f"{x['window_fit_mm']:6.1f}"
            print(f"  {name:13s} baseline {wf(out['summary_json_baseline'].get(name))} (reproduced "
                  f"{wf(out['baseline_reproduced'].get(name))})  elevation {wf(out['summary_json'].get(name))}  "
                  f"OPERA {wf(out['opera'].get(name))}  px {out['opera'].get(name, {}).get('pixels')}")
    (HERE / "tropo_opera.json").write_text(json.dumps(result, indent=1, default=float) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
