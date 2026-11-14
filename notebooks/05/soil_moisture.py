# Owner: 05 · Validator (Paul)
# Exploration only (never imported). Red-team check: is part of the Sentinel-1 "sinking" really soil moisture?
#   python notebooks/05/soil_moisture.py            # needs EARTHDATA_TOKEN in .env (never printed, never committed)
# Reads NISAR L3 SME2 soil moisture (200 m EASE-Grid 2.0) over HTTP, cuts the Sentinel-1 window (16.4 km around
# 45.088 N, 24.290 E), and writes data/work/ocnele_mari/sm/sm_zones.csv (local) and docs/figures/05_soil_moisture.png.
"""Soil moisture per zone and in the Sentinel-1 reference band, on every NISAR SME2 date over the town.

Only pixels whose retrievalQualityFlag says "recommended" (least significant bit 0) are used. Zones are the circles in
common.py, widened by 100 m because the moisture pixels are 200 m wide. The reference band is the one
sentinel1/scripts/fit.py zeroes each pair on: 3 to 6.5 km from the nearest zone edge. Units: m3/m3 (0.25 = 25 %).
"""
from __future__ import annotations

import json
import pathlib
import re
import struct
import sys
import urllib.request
import warnings

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import common as C  # noqa: E402

warnings.filterwarnings("ignore")
SITE = C.SITES["ocnele_mari"]
HALF_M = 8200            # Sentinel-1 analysis window half-size (sentinel1/scripts/fit.py)
REF_BAND_M = (3000, 6500)
SEARCH = ("https://api.daac.asf.alaska.edu/services/search/param?intersectsWith=POINT(24.29666%2045.08846)"
          "&platform=NISAR&processingLevel=SME2&maxResults=200&output=json")


def token() -> str:
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        m = re.match(r"\s*EARTHDATA_TOKEN\s*=\s*['\"]?([^'\"\s]+)", line)
        if m:
            return m.group(1)
    raise SystemExit("EARTHDATA_TOKEN missing in .env")


def patch_pyfive():
    """pyfive 0.4 memory-maps contiguous arrays, which needs a local file; read them with seek/read instead."""
    from pyfive import dataobjects as D
    original = D.DataObjects._get_contiguous_data

    def contiguous(self, property_offset):
        if isinstance(self.dtype, tuple):
            return original(self, property_offset)
        off, = struct.unpack_from("<Q", self.msg_data, property_offset)
        n = int(np.prod(self.shape)) * np.dtype(self.dtype).itemsize
        self.fh.seek(off)
        return np.frombuffer(self.fh.read(n), dtype=self.dtype).reshape(self.shape)
    D.DataObjects._get_contiguous_data = contiguous


def granules() -> list[dict]:
    with urllib.request.urlopen(SEARCH, timeout=120) as r:
        rows = json.load(r)[0]
    out = [dict(url=g["downloadUrl"], date=g["startTime"][:10],
                track=f"{int(g['track']):03d}{g['flightDirection'][0]}") for g in rows]
    return sorted(out, key=lambda g: g["date"])


def masks(lat, lon):
    """Zone masks (r + 100 m), the reference band and the window, on the lat/lon grid of the cut."""
    LA, LO = np.meshgrid(lat, lon, indexing="ij")
    def d(la, lo):
        return 111_320 * np.hypot(LA - la, (LO - lo) * np.cos(np.radians(la)))
    edge = np.min([d(z["lat"], z["lon"]) - z["r_m"] for z in SITE["zones"]], axis=0)
    m = {z["id"]: d(z["lat"], z["lon"]) <= z["r_m"] + 100 for z in SITE["zones"]}
    m["ref_band"] = (edge >= REF_BAND_M[0]) & (edge <= REF_BAND_M[1])
    m["control"] = (edge > REF_BAND_M[1]) & (edge <= 8000)   # fit.py's outer control: stable ground for the test
    m["window"] = np.ones_like(edge, bool)
    return m


def read_one(fs, g) -> dict:
    import pyfive
    with fs.open(g["url"], "rb", block_size=2 ** 20, cache_type="blockcache") as f:
        grids = pyfive.File(f)["science/LSAR/SME2/grids"]
        lat, lon = grids["latitude"][:], grids["longitude"][:]
        dlat, dlon = HALF_M / 111_320, HALF_M / (111_320 * np.cos(np.radians(SITE["lat"])))
        r = np.where(np.abs(lat - SITE["lat"]) <= dlat)[0]
        c = np.where(np.abs(lon - SITE["lon"]) <= dlon)[0]
        if not len(r) or not len(c):
            return dict(g, note="town outside this frame")
        rs, cs = slice(r.min(), r.max() + 1), slice(c.min(), c.max() + 1)
        sm = np.array(grids["soilMoisture"][:][rs, cs], float)
        unc = np.array(grids["soilMoistureUncertainty"][:][rs, cs], float)
        flag = np.array(grids["retrievalQualityFlag"][:][rs, cs])
    ok = (sm > -9000) & (flag >= 0) & ((flag & 1) == 0)
    row = dict(g)
    any_ok = (sm > -9000) & (flag >= 0)   # sensitivity only: also the retrievals NISAR does not recommend
    for k, m in masks(lat[rs], lon[cs]).items():
        v = sm[m & ok]
        row[f"{k}_sm"] = round(float(np.median(v)), 4) if v.size else None
        row[f"{k}_n"] = int(v.size)
        row[f"{k}_unc"] = round(float(np.median(unc[m & ok])), 4) if v.size else None
        va = sm[m & any_ok]
        row[f"{k}_sm_all"] = round(float(np.median(va)), 4) if va.size else None
        row[f"{k}_n_all"] = int(va.size)
    return row


def main():
    import csv

    import fsspec
    import aiohttp
    patch_pyfive()
    # a stalled HTTP read used to hang forever: give every read 60 s, and retry a file up to 3 times
    fs = fsspec.filesystem("http", headers={"Authorization": f"Bearer {token()}"},
                           client_kwargs={"timeout": aiohttp.ClientTimeout(total=None, sock_connect=30, sock_read=60)})
    out = C.site_dir("ocnele_mari", "sm") / "sm_zones.csv"
    done = {}
    if out.exists():
        with open(out, encoding="utf-8") as f:
            done = {r["url"]: r for r in csv.DictReader(f)}
    rows = []
    for g in granules():
        # reuse a saved date unless it lacks the control ring and falls in the Sentinel-1 window (Jul to early Oct)
        old = done.get(g["url"])
        if old and (old.get("control_n", "") != "" or not "2026-07-01" <= g["date"] <= "2026-10-10"):
            rows.append(done[g["url"]])
            continue
        for attempt in range(3):
            try:
                row = read_one(fs, g)
                break
            except Exception as e:  # network hiccup: try again, then record the failure and move on
                print(f"{g['date']} {g['track']}: attempt {attempt + 1} failed ({type(e).__name__})", flush=True)
                row = dict(g, note=f"read failed: {type(e).__name__}")
        if "note" in row and row["note"].startswith("read failed"):
            continue  # not saved, so the next run tries it again
        rows.append(row)
        print(f"{row['date']} {row['track']}: window {row.get('window_sm')} m3/m3 ({row.get('window_n')} px), "
              f"ref band {row.get('ref_band_sm')}, z1..z4 "
              + ", ".join(f"{row.get(z['id'] + '_sm')}" for z in SITE["zones"]), flush=True)
        keys = sorted({k for r in rows for k in r})
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
    print(f"→ {out} ({len(rows)} dates)")


if __name__ == "__main__":
    main()
