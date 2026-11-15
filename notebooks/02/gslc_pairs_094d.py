# Owner: 02 · NISAR data (Alexandru, Eric)
"""Exploration only (never imported). Our own NISAR 094D pairs from the raw geocoded single-look data (GSLC), to test
independently whether the 094D zones really read positive (the phase-sign test T3 failed on NASA's interferograms).

    python notebooks/02/gslc_pairs_094d.py          (Earthdata token as for fetch.py; about 400 MB read)

What it does, with nothing tuned to the result:
1. Reads the HH channel of every 094D GSLC (NISAR_L2_GSLC_PROVISIONAL_V1, 10 dates, 20 Jun to 18 Oct 2026) in a
   12 x 12 km box around the four zones, by HTTP range reads (each file is about 12 GB; only the box is read).
2. Multilooks to 80 m (8 x 16 looks on the 10 m x 5 m grid) and forms every pair up to 36 days apart: a redundant
   network (12-, 24- and 36-day pairs), unlike NASA's single chain, so closure triplets exist.
3. Removes each pair's phase relative to the stable reference (no unwrapping: at L-band one cycle is 12 cm of line of
   sight, and the share of pixels near ±π is reported as a check).
4. Runs stack.py's own cleaning (coherence 0.35, elevation slope, stable ground outside the zones + 3 km = 0),
   inversion and rate, then the T3 rule unchanged: zone-median line-of-sight rate below −2 mm/yr.
5. Sign check first: one 12-day GSLC pair is correlated with NASA's GUNW interferogram for the same dates.
Writes notebooks/02/gslc_pairs_094d.json.
"""
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402

import common as C  # noqa: E402
import export  # noqa: E402
import fetch  # noqa: E402
import split  # noqa: E402
import stack  # noqa: E402

SITE, TRACK, HALF_M, LX, LY, MAX_DAYS = "ocnele_mari", "094D", 6000, 8, 16, 36
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"


def granules():
    import requests
    r = requests.get(CMR, params=dict(short_name="NISAR_L2_GSLC_PROVISIONAL_V1", point="24.290,45.088", page_size=200), timeout=60)
    out = {}
    for e in r.json()["feed"]["entry"]:
        if "_094_D_" in e["title"]:
            url = next(l["href"] for l in e["links"] if l["href"].endswith(".h5") and l["href"].startswith("https"))
            out[e["time_start"][:10].replace("-", "")] = url
    return dict(sorted(out.items()))


def box(site, epsg):
    zs = C.SITES[site]["zones"]
    xy = [C.to_xy(epsg, z["lon"], z["lat"]) for z in zs]
    cx, cy = np.mean([p[0] for p in xy]), np.mean([p[1] for p in xy])
    return cx - HALF_M, cx + HALF_M, cy - HALF_M, cy + HALF_M


def read_date(url, site):
    h5, rf = fetch.open_h5(url, None)
    g = h5["science/LSAR/GSLC/grids/frequencyA"]
    epsg = int(g["projection"][()])                 # GSLC frame 066 is in UTM 34N, not the GUNW's 35N
    bx = box(site, epsg)
    x, y = g["xCoordinates"][()], g["yCoordinates"][()]
    c0, c1 = int(np.searchsorted(x, bx[0])), int(np.searchsorted(x, bx[1]))
    r0, r1 = int(np.searchsorted(-y, -bx[3])), int(np.searchsorted(-y, -bx[2]))
    c1 = c0 + (c1 - c0) // LX * LX; r1 = r0 + (r1 - r0) // LY * LY
    slc = g["HH"][r0:r1, c0:c1]
    return slc, x[c0:c1], y[r0:r1], rf.fetched, epsg


def multilook(a):
    ny, nx = a.shape[0] // LY, a.shape[1] // LX
    return a[:ny * LY, :nx * LX].reshape(ny, LY, nx, LX).mean(axis=(1, 3))


def main():
    gr = granules()
    slcs, xs, ys, mb = {}, None, None, 0
    for d, url in gr.items():
        s, x, y, n, epsg = read_date(url, SITE)
        if xs is not None and (len(x) != len(xs) or abs(x[0] - xs[0]) > 1 or abs(y[0] - ys[0]) > 1):
            raise SystemExit(f"{d}: GSLC grid differs from the first date; stop")
        slcs[d], xs, ys, mb = s, x, y, mb + n
        print(f"{d}: {s.shape} read, {n / 1e6:.0f} MB", flush=True)
    dates = sorted(slcs)
    meta = dict(epsg=epsg, x0=float(xs[:LX].mean()), y0=float(ys[:LY].mean()), dx=float(xs[LX] - xs[0]),
                dy=float(ys[LY] - ys[0]), nx=len(xs) // LX, ny=len(ys) // LY, wavelength=0.24393, synthetic=False)
    from datetime import date
    dd = lambda d: date(int(d[:4]), int(d[4:6]), int(d[6:]))
    pairs = [(a, b) for i, a in enumerate(dates) for b in dates[i + 1:] if (dd(b) - dd(a)).days <= MAX_DAYS]
    pw = {d: multilook(np.abs(slcs[d]) ** 2) for d in dates}
    stable = stack.stable_mask(SITE, meta)
    phase, coh, wrapped = [], [], []
    for a, b in pairs:
        ifg = multilook(slcs[a] * np.conj(slcs[b]))
        c = np.abs(ifg) / np.sqrt(pw[a] * pw[b])
        ref = ifg[stable & (c >= C.MIN_COH)]
        ph = np.angle(ifg * np.conj(ref.sum() / np.abs(ref.sum())))
        phase.append(ph.astype("f4")); coh.append(c.astype("f4"))
        wrapped.append(float((np.abs(ph[c >= C.MIN_COH]) > 2.5).mean()))
    data = dict(phase=np.stack(phase), coh=np.stack(coh), qa=[{}] * len(pairs))
    # DEM on this grid from the 094D GUNW DEM (80 m), nearest neighbour
    gmeta = C.load_json(C.WORK / SITE / TRACK / "meta.json")
    dem = split.resample(gmeta, np.load(C.WORK / SITE / TRACK / "dem.npz")["dem"], meta)
    # sign check: the first 12-day GSLC pair against NASA's GUNW interferogram for the same dates
    first = next((p for p in pairs if (dd(p[1]) - dd(p[0])).days == 12), None)
    gunw = np.load(C.WORK / SITE / TRACK / f"{first[0]}_{first[1]}.npz")["phase"]
    gunw_here = split.resample(gmeta, gunw, meta)
    k = pairs.index(first)
    ok = np.isfinite(gunw_here) & (data["coh"][k] >= C.MIN_COH)
    gw = gunw_here[ok] - np.median(gunw_here[ok]); gs = data["phase"][k][ok] - np.median(data["phase"][k][ok])
    sign_r = float(np.corrcoef(gw, gs)[0, 1])
    mm, slopes = stack.to_mm_and_clean(SITE, meta, data, dem)
    groups = stack.groups_of(pairs, dates)
    cum = stack.invert(pairs, dates, mm, groups)
    vel, sig, _ = stack.fit_rate(dates, cum, groups)
    masks = export.nisar_zone_masks(C.SITES[SITE], meta)
    zones = {z: round(float(np.median(vel[masks[z] & np.isfinite(vel)])), 2) for z in ("z1", "z2", "z3", "z4") if (masks[z] & np.isfinite(vel)).sum() >= 3}
    pooled = np.concatenate([vel[masks[z] & np.isfinite(vel)] for z in ("z1", "z2", "z3", "z4")])
    trip = [(a, b, c) for (a, b) in pairs for (b2, c) in pairs if b2 == b and (a, c) in pairs]
    clos = []
    for a, b, c in trip:
        i1, i2, i3 = pairs.index((a, b)), pairs.index((b, c)), pairs.index((a, c))
        cl = np.angle(np.exp(1j * (data["phase"][i1] + data["phase"][i2] - data["phase"][i3])))
        m = (data["coh"][[i1, i2, i3]] >= C.MIN_COH).all(0)
        clos.append(float(np.median(np.abs(cl[m])) * 0.24393 / (4 * np.pi) * 1000))
    r = float(np.median(pooled))
    out = dict(source="NISAR_L2_GSLC_PROVISIONAL_V1, HH, 094D", dates=dates, pairs=[f"{a}_{b}" for a, b in pairs],
               box_km=2 * HALF_M / 1000, looks=[LX, LY], mb_read=round(mb / 1e6), sign_check_r_vs_gunw=round(sign_r, 3),
               share_near_pi=round(float(np.mean(wrapped)), 3), triplets=len(trip),
               closure_median_abs_mm=round(float(np.median(clos)), 2) if clos else None,
               zones_mm_yr=zones, zones_pooled_mm_yr=round(r, 2), pixels=int(pooled.size),
               t3_pass=bool(r < -2), rule="T3 unchanged: zone-median LOS rate below -2 mm/yr, stable ground outside the zones + 3 km as reference")
    (ROOT / "notebooks" / "02" / "gslc_pairs_094d.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("dates", "pairs")}, indent=1))


if __name__ == "__main__":
    main()
