# Owner: 04 · Geodesist (Matei)
"""Exploration only (never imported). Do pair errors add up along NASA's chain of 12-day pairs?

    python notebooks/04/gslc_chain_vs_network.py        (Earthdata token from .env; about 300 MB read once, cached)

The test, on one dataset: NISAR 094D raw single-look data (GSLC, 10 dates, 20 Jun to 18 Oct 2026), read and
multilooked exactly as 02's notebooks/02/gslc_pairs_094d.py does (same 12 x 12 km box, 8 x 16 looks to 80 m, same
reference to stable ground). Then the same stack.py cleaning, inversion and rate, twice:
  - chain:   one 12-day (or 24-day) pair from each date to the next, as in NASA's interferograms;
  - network: every pair up to 36 days apart (21 pairs, 16 closure triplets), as in 02's notebook.
For each, the noise of a zone's rate from fake zones on stable ground (300 m disc minus a 0.5 to 1.5 km ring; the
12 km box is too small for noise_floor.py's 1 to 3 km ring), and how the zone-to-zone spread of cumulative
displacement grows with the number of pairs. If pair errors add up, the chain's spread grows like √(pairs) and its
rate noise is clearly larger than the network's.

Reads data/work/ocnele_mari/094D/ (meta.json, dem.npz) for the DEM. Caches the interferograms in
data/work/ocnele_mari/r04/gslc094d_ifgs.npz (git-ignored). Writes notebooks/04/gslc_chain_vs_network.json.
Credit: the reading and pair forming follow 02's notebook (Alexandru, Eric).
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402

import common as C  # noqa: E402
import fetch  # noqa: E402
import split  # noqa: E402
import stack  # noqa: E402
from noise_floor import chain_step_sigma, rate_sigma_factor, robust_sigma  # noqa: E402

SITE, TRACK, HALF_M, LX, LY, MAX_DAYS = "ocnele_mari", "094D", 6000, 8, 16, 36
CACHE = C.WORK / SITE / "r04" / "gslc094d_ifgs.npz"
OUT = ROOT / "notebooks" / "04" / "gslc_chain_vs_network.json"
ZONE_R, RING, DRAWS = 300.0, (500.0, 1500.0), 1000
dd = lambda d: date(int(d[:4]), int(d[4:6]), int(d[6:]))


def token():
    """EARTHDATA_TOKEN from the environment or .env (never printed)."""
    if os.environ.get("EARTHDATA_TOKEN"):
        return os.environ["EARTHDATA_TOKEN"]
    env = ROOT / ".env"
    for line in env.read_text(encoding="utf-8").splitlines() if env.exists() else []:
        if line.strip().startswith("EARTHDATA_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def granules():
    import requests
    r = requests.get("https://cmr.earthdata.nasa.gov/search/granules.json", timeout=60,
                     params=dict(short_name="NISAR_L2_GSLC_PROVISIONAL_V1", point="24.290,45.088", page_size=200))
    out = {}
    for e in r.json()["feed"]["entry"]:
        if "_094_D_" in e["title"]:
            url = next(l["href"] for l in e["links"] if l["href"].endswith(".h5") and l["href"].startswith("https"))
            out[e["time_start"][:10].replace("-", "")] = url
    return dict(sorted(out.items()))


def multilook(a):
    ny, nx = a.shape[0] // LY, a.shape[1] // LX
    return a[:ny * LY, :nx * LX].reshape(ny, LY, nx, LX).mean(axis=(1, 3))


def read_all():
    """Read every date's HH box once; return the multilooked interferograms of every pair up to MAX_DAYS."""
    tok = token()
    slcs, xs, ys, mb, epsg = {}, None, None, 0, None
    for d, url in granules().items():
        h5, rf = fetch.open_h5(url, tok)
        g = h5["science/LSAR/GSLC/grids/frequencyA"]
        epsg = int(g["projection"][()])
        zs = [C.to_xy(epsg, z["lon"], z["lat"]) for z in C.SITES[SITE]["zones"]]
        cx, cy = np.mean([p[0] for p in zs]), np.mean([p[1] for p in zs])
        x, y = g["xCoordinates"][()], g["yCoordinates"][()]
        c0, c1 = int(np.searchsorted(x, cx - HALF_M)), int(np.searchsorted(x, cx + HALF_M))
        r0, r1 = int(np.searchsorted(-y, -(cy + HALF_M))), int(np.searchsorted(-y, -(cy - HALF_M)))
        c1 = c0 + (c1 - c0) // LX * LX
        r1 = r0 + (r1 - r0) // LY * LY
        s = g["HH"][r0:r1, c0:c1]
        x, y = x[c0:c1], y[r0:r1]
        if xs is not None and (len(x) != len(xs) or abs(x[0] - xs[0]) > 1 or abs(y[0] - ys[0]) > 1):
            raise SystemExit(f"{d}: GSLC grid differs from the first date; stop")
        slcs[d], xs, ys, mb = s, x, y, mb + rf.fetched
        print(f"{d}: {s.shape} read, {rf.fetched / 1e6:.0f} MB", flush=True)
    dates = sorted(slcs)
    meta = dict(epsg=epsg, x0=float(xs[:LX].mean()), y0=float(ys[:LY].mean()), dx=float(xs[LX] - xs[0]),
                dy=float(ys[LY] - ys[0]), nx=len(xs) // LX, ny=len(ys) // LY, wavelength=0.24393, synthetic=False)
    pairs = [(a, b) for i, a in enumerate(dates) for b in dates[i + 1:] if (dd(b) - dd(a)).days <= MAX_DAYS]
    pw = {d: multilook(np.abs(slcs[d]) ** 2) for d in dates}
    ifg = np.stack([multilook(slcs[a] * np.conj(slcs[b])) for a, b in pairs]).astype("c8")
    coh = np.stack([np.abs(ifg[k]) / np.sqrt(pw[a] * pw[b]) for k, (a, b) in enumerate(pairs)]).astype("f4")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, ifg=ifg, coh=coh, dates=np.array(dates), pairs=np.array([f"{a}_{b}" for a, b in pairs]),
                        meta=json.dumps(meta), mb=mb)
    return ifg, coh, dates, pairs, meta, mb


def load():
    if CACHE.exists():
        z = np.load(CACHE)
        pairs = [tuple(p.split("_")) for p in z["pairs"]]
        return z["ifg"], z["coh"], [str(d) for d in z["dates"]], pairs, json.loads(str(z["meta"])), int(z["mb"])
    return read_all()


def run_network(name, keep, ifg, coh, dates, pairs, meta, dem, stable):
    idx = [k for k, p in enumerate(pairs) if keep(p)]
    sub = [pairs[k] for k in idx]
    phase = []
    for k in idx:
        ref = ifg[k][stable & (coh[k] >= C.MIN_COH)]
        phase.append(np.angle(ifg[k] * np.conj(ref.sum() / np.abs(ref.sum()))).astype("f4"))
    data = dict(phase=np.stack(phase), coh=coh[idx], qa=[{}] * len(sub))
    mm, _ = stack.to_mm_and_clean(SITE, meta, data, dem)
    groups = stack.groups_of(sub, dates)
    cum = stack.invert(sub, dates, mm, groups)
    vel, _, _ = stack.fit_rate(dates, cum, groups)
    return sub, groups, cum, vel


def fake_zones(vel, cum, stable, meta, rng):
    """Zone-minus-ring rates and cumulative series of random 300 m discs on stable ground."""
    ny, nx = vel.shape
    k = int(np.ceil(RING[1] / abs(meta["dx"]))) + 1
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    d = np.hypot(xx * meta["dx"], yy * meta["dy"])
    disc_o, ring_o = d <= ZONE_R, (d > RING[0]) & (d <= RING[1])
    good = stable & np.isfinite(vel)
    ys, xs = np.nonzero(good[k:ny - k, k:nx - k])
    rates, series = [], []
    for i in rng.permutation(len(ys)):
        r, c = ys[i] + k, xs[i] + k
        sl = (slice(r - k, r + k + 1), slice(c - k, c + k + 1))
        g = good[sl]
        dm, rm = disc_o & g, ring_o & g
        if dm.sum() < 10 or rm.sum() < 20:
            continue
        rates.append(np.median(vel[sl][dm]) - np.median(vel[sl][rm]))
        series.append(np.nanmedian(cum[(slice(None),) + sl][:, dm], 1) - np.nanmedian(cum[(slice(None),) + sl][:, rm], 1))
        if len(rates) >= DRAWS:
            break
    return np.array(rates), np.array(series)


def main():
    ifg, coh, dates, pairs, meta, mb = load()
    gmeta = C.load_json(C.WORK / SITE / TRACK / "meta.json")
    dem = split.resample(gmeta, np.load(C.WORK / SITE / TRACK / "dem.npz")["dem"], meta)
    stable = stack.stable_mask(SITE, meta)
    nxt = {a: b for a, b in zip(dates, dates[1:])}
    nets = {"chain": lambda p: nxt.get(p[0]) == p[1], "network": lambda p: True}
    t = np.asarray(C.years([f"{d[:4]}-{d[4:6]}-{d[6:]}" for d in dates]), float)
    out = dict(source="NISAR_L2_GSLC_PROVISIONAL_V1, HH, 094D, 12 x 12 km box, 80 m (as notebooks/02/gslc_pairs_094d.py)",
               dates=dates, mb_read=round(mb / 1e6), zone_r_m=ZONE_R, ring_m=list(RING), draws=DRAWS, seed=2026,
               stable_pixels=int(stable.sum()), runs={})
    built = {name: run_network(name, keep, ifg, coh, dates, pairs, meta, dem, stable) for name, keep in nets.items()}
    common = np.logical_and.reduce([np.isfinite(b[3]) for b in built.values()])
    out["common_pixels"] = int((common & stable).sum())
    for name, (sub, groups, cum, vel) in built.items():
        g = list(np.asarray(groups).tolist()) if not isinstance(groups, list) else groups
        for tag, mask in (("own_pixels", np.isfinite(vel)), ("common_pixels", common)):
            v = np.where(mask, vel, np.nan)
            rates, series = fake_zones(v, cum, stable, meta, np.random.default_rng(2026))
            spread = [round(robust_sigma(series[:, i]), 2) for i in range(series.shape[1])]
            sig = robust_sigma(rates)
            out["runs"].setdefault(name, dict(pairs=len(sub), pair_days=sorted({(dd(b) - dd(a)).days for a, b in sub})))
            out["runs"][name][tag] = dict(
                fake_zones=len(rates), zone_rate_sigma_mm_yr=round(sig, 2), spread_by_date_mm=spread,
                per_pair_sigma_from_spread_growth_mm=round(chain_step_sigma(g, series), 2),
                rate_sigma_if_chain_random_walk_mm_yr=round(chain_step_sigma(g, series) * rate_sigma_factor(t, g, True), 2),
                rate_sigma_if_independent_dates_mm_yr=round(robust_sigma(series[:, 1]) / np.sqrt(2) * rate_sigma_factor(t, g, False), 2))
            print(f"{name} [{tag}]: {len(sub)} pairs · {len(rates)} fake zones · zone rate σ {sig:.1f} mm/yr · "
                  f"random-walk model {out['runs'][name][tag]['rate_sigma_if_chain_random_walk_mm_yr']} · "
                  f"independent-dates model {out['runs'][name][tag]['rate_sigma_if_independent_dates_mm_yr']} · spread {spread}")
    c, n = out["runs"]["chain"]["common_pixels"], out["runs"]["network"]["common_pixels"]
    out["ratio_chain_over_network_common_pixels"] = round(c["zone_rate_sigma_mm_yr"] / n["zone_rate_sigma_mm_yr"], 2)
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"common pixels {out['common_pixels']} · chain / network rate σ = "
          f"{out['ratio_chain_over_network_common_pixels']} · wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
