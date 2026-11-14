# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""03 · InSAR analyst: pairs → displacement time series and rate ± σ, per track.

Status: WORKING on real data (14 Nov 2026), our own small-baseline inversion (O-05: not MintPy).

    python stack.py ocnele_mari            # every fetched track
    python stack.py ocnele_mari --track 129A
    python stack.py ocnele_mari --sign +1  # rerun with the other phase sign (T3 test only)

Reads data/work/<site>/<track>/ from fetch.py (meta.json, <ref>_<sec>.npz, dem.npz).
Writes data/work/<site>/<track>/ts.npz. The hand-off to 04, 05 and 06:
    dates (str YYYY-MM-DD), cum (date, y, x) mm towards the satellite, each acquisition group starting at 0 on its
    first date; vel / vel_sig (mm/yr); annual_amp (mm, NaN under C.ANNUAL_TERM_MIN_YEARS); rate12 / rate24 and
    n_triplets (closure; 0 triplets here, so NaN); coh_mean, valid_share; gaps (str); n_pairs, pair_days;
    tropo_mm_per_100m (per pair, removed); group (one per date), gap_ranges, pairs, iono_used, phase_sign,
    reference, made_by (fields 04 added on 14 Nov; kept)

Method:
1. mm = PHASE_SIGN · phase · λ/4π · 1000. The sign is tested (T3, docs/validation-log.md), not assumed.
2. Mask coherence under C.MIN_COH. Remove the elevation-correlated troposphere per pair: a robust slope against the DEM
   on stable ground (outside every zone + C.EXCLUDE_KM). Then reference each pair to the median of that stable ground.
3. Small-baseline inversion per pixel: dates no pair connects form separate groups; each group's first date is 0.
   A pixel needs C.MIN_VALID_PAIRS of the pairs. Dates its valid pairs connect to their group's first date get a
   value; dates cut off by a low-coherence pair are NaN (partial series, not a dropped pixel).
4. Rate = straight line THROUGH THE DATES with one offset per group (never fitted to the pairs).
5. No annual term under C.ANNUAL_TERM_MIN_YEARS. σ assumes independent dates: a lower bound.
"""
from __future__ import annotations

import argparse

import common as C

PHASE_SIGN = -1   # DRAFT: LOS mm (towards satellite) = PHASE_SIGN · phase · λ/4π. Tested by T3 (validate check 1).
MIN_RATE_DATES, MIN_RATE_SPAN_YR = 6, 0.3   # a partial series needs this many dates over this span for a rate


def _iso(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}"


def load_pairs(site: str, track: str):
    """→ (meta, pairs [(ref, sec)], data {phase, coh, qa}, dem or None) for one track."""
    import numpy as np
    d = C.WORK / site / track
    meta = C.load_json(d / "meta.json")
    files = sorted(p for p in d.glob("????????_????????.npz"))
    if not files:
        raise C.todo("02", f"no pair files under {d}: run fetch.py first")
    pairs, phase, coh, qa = [], [], [], []
    for f in files:
        z = np.load(f)
        pairs.append(tuple(f.stem.split("_")))
        phase.append(z["phase"]); coh.append(z["coh"])
        qa.append({k: z[k].item() for k in ("iono_used", "iono_std", "valid_share", "main_share", "iono_interp")})
    dem = None
    if (d / "dem.npz").exists():                     # fetch.py writes "dem"; older stand-ins wrote "height"
        z = np.load(d / "dem.npz")
        dem = z["dem"] if "dem" in z.files else z["height"]
    return meta, pairs, dict(phase=np.stack(phase), coh=np.stack(coh), qa=qa), dem


def stable_mask(site: str, meta: dict):
    """Pixels outside every salt zone + C.EXCLUDE_KM (the tie rule of calibrate.py, without the stations)."""
    import numpy as np
    x = meta["x0"] + np.arange(meta["nx"]) * meta["dx"]
    y = meta["y0"] + np.arange(meta["ny"]) * meta["dy"]
    X, Y = np.meshgrid(x, y)
    far = np.ones(X.shape, bool)
    for z in C.SITES[site]["zones"]:
        zx, zy = C.to_xy(meta["epsg"], z["lon"], z["lat"])
        far &= np.hypot(X - zx, Y - zy) > z["r_m"] + C.EXCLUDE_KM * 1000
    return far


def to_mm_and_clean(site: str, meta: dict, data: dict, dem, sign: int = PHASE_SIGN):
    """Phase → LOS mm; mask low coherence (C.MIN_COH); remove the elevation slope; reference to stable ground."""
    import numpy as np
    mm = sign * data["phase"] * meta["wavelength"] / (4 * np.pi) * 1000.0
    mm = np.where(data["coh"] >= C.MIN_COH, mm, np.nan).astype("f4")
    stable = stable_mask(site, meta)
    slopes = []
    for k in range(len(mm)):
        m = mm[k]
        ok = stable & np.isfinite(m)
        s = 0.0
        if dem is not None:
            ok &= np.isfinite(dem)
            h, v = dem[ok], m[ok]
            if h.size > 1000:
                for _ in range(2):                      # least squares, then once more without 3σ outliers
                    A = np.c_[h - np.median(h), np.ones_like(h)]
                    c = np.linalg.lstsq(A, v, rcond=None)[0]
                    r = v - A @ c
                    keep = np.abs(r - np.median(r)) < 3 * 1.4826 * np.median(np.abs(r - np.median(r)))
                    h, v = h[keep], v[keep]
                s = float(c[0])
                m = m - s * (dem - np.nanmedian(dem[stable]))
        m = m - np.nanmedian(m[stable & np.isfinite(m)])
        mm[k] = m
        slopes.append(s * 100)                           # mm per 100 m
    return mm, np.array(slopes)


def groups_of(pairs, dates):
    """Label each date with its connected component in the pair graph (dates no pair connects split groups)."""
    parent = {d: d for d in dates}
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a, b in pairs:
        parent[find(a)] = find(b)
    roots = []
    for d in dates:
        r = find(d)
        if r not in roots:
            roots.append(r)
    return [roots.index(find(d)) for d in dates]


def invert(pairs, dates, mm, groups):
    """Small-baseline inversion: pairs → cumulative displacement per date, each group's first date at 0."""
    import numpy as np
    P, ny, nx = mm.shape
    D = len(dates)
    idx = {d: i for i, d in enumerate(dates)}
    G = np.zeros((P, D))
    for k, (a, b) in enumerate(pairs):
        G[k, idx[b]] += 1
        G[k, idx[a]] -= 1
    firsts = [dates.index(next(d for d, g in zip(dates, groups) if g == gg)) for gg in sorted(set(groups))]
    free = [i for i in range(D) if i not in firsts]
    Gf = G[:, free]
    flat = mm.reshape(P, -1)
    ok = np.isfinite(flat)
    enough = ok.mean(0) >= C.MIN_VALID_PAIRS
    cum = np.full((D, flat.shape[1]), np.nan, "f4")
    pattern = np.packbits(ok, axis=0)
    keys, inv = np.unique(pattern, axis=1, return_inverse=True)
    inv = inv.ravel()
    gid = {i: g for i, g in enumerate(groups)}
    for u in range(keys.shape[1]):
        cols = np.where((inv == u) & enough)[0]
        if not cols.size:
            continue
        rows = ok[:, cols[0]]
        # Dates this pixel's valid pairs connect to their group's first date. A pair under C.MIN_COH breaks a chain
        # (129A is a single chain of 13 pairs), so instead of dropping the whole pixel, keep the dates still reached
        # and leave the rest NaN. Before this, one broken pair out of 13 removed about 70 % of the town.
        reach = set(firsts)
        grew = True
        while grew:
            grew = False
            for k, (a, b) in enumerate(pairs):
                if rows[k] and (idx[a] in reach) != (idx[b] in reach):
                    reach |= {idx[a], idx[b]}
                    grew = True
        lonely = {f for f in firsts if not any(i in reach for i in range(D) if gid[i] == gid[f] and i != f)}
        reach -= lonely                                  # a group's first date alone carries no displacement
        use_free = [i for i in free if i in reach]
        c = np.full((D, cols.size), np.nan, "f4")
        for f in firsts:
            if f in reach:
                c[f] = 0.0
        if use_free:
            prow = rows & np.array([idx[a] in reach and idx[b] in reach for a, b in pairs])
            A = G[prow][:, use_free]
            if np.linalg.matrix_rank(A) < len(use_free):
                continue
            c[use_free] = np.linalg.lstsq(A, flat[prow][:, cols], rcond=None)[0]
        cum[:, cols] = c
    return cum.reshape(D, ny, nx)


def fit_rate(dates, cum, groups):
    """Line through the dates with one offset per group → vel, vel_sig (lower bound), annual_amp (NaN if short)."""
    import numpy as np
    t = C.years([_iso(d) for d in dates])
    D = len(dates)
    ng = len(set(groups))
    A = np.c_[t, np.eye(ng)[groups]]
    flat = cum.reshape(D, -1)
    ok = np.isfinite(flat)
    vel = np.full(flat.shape[1], np.nan, "f4")
    sig = np.full(flat.shape[1], np.nan, "f4")
    keys, inv = np.unique(np.packbits(ok, axis=0), axis=1, return_inverse=True)
    inv = inv.ravel()
    for u in range(keys.shape[1]):
        cols = np.where(inv == u)[0]
        rows = ok[:, cols[0]]
        if rows.sum() < MIN_RATE_DATES or np.ptp(t[rows]) < MIN_RATE_SPAN_YR:
            continue                                 # partial series too short for a rate (the dates still show)
        Au = A[rows][:, np.abs(A[rows]).sum(0) > 0]
        if rows.sum() <= Au.shape[1] or np.linalg.matrix_rank(Au) < Au.shape[1]:
            continue
        c, *_ = np.linalg.lstsq(Au, flat[rows][:, cols], rcond=None)
        r = flat[rows][:, cols] - Au @ c
        dof = rows.sum() - Au.shape[1]
        cov00 = np.linalg.inv(Au.T @ Au)[0, 0]
        vel[cols] = c[0]
        sig[cols] = np.sqrt((r ** 2).sum(0) / dof * cov00)
    span = t[-1] - t[0]
    amp = np.full(flat.shape[1], np.nan, "f4")              # no annual term below C.ANNUAL_TERM_MIN_YEARS
    if span >= C.ANNUAL_TERM_MIN_YEARS:
        raise C.todo("03", "annual term for spans of 1.5 years or more")
    shp = cum.shape[1:]
    return vel.reshape(shp), sig.reshape(shp), amp.reshape(shp)


def closure(pairs, dates, data):
    """Triplets (two 12-day pairs + the 24-day pair over the same dates) → rate12, rate24, n_triplets.

    Ocnele Mari's GUNW stack has 0 triplets (the 24-day pairs replace missing 12-day pairs), so this reports
    'not tested' unless a triplet appears.
    """
    have = set(pairs)
    trip = [(a, b, c) for (a, b) in pairs for (b2, c) in pairs if b2 == b and (a, c) in have]
    return len(trip)


def run(site: str, track: str, sign: int = PHASE_SIGN, out_name: str = "ts.npz") -> dict:
    import numpy as np
    meta, pairs, data, dem = load_pairs(site, track)
    mm, slopes = to_mm_and_clean(site, meta, data, dem, sign)
    dates = sorted({d for p in pairs for d in p})
    groups = groups_of(pairs, dates)
    cum = invert(pairs, dates, mm, groups)
    vel, sig, amp = fit_rate(dates, cum, groups)
    ntrip = closure(pairs, dates, data)
    breaks = [(dates[i - 1], dates[i]) for i in range(1, len(dates)) if groups[i] != groups[i - 1]]
    coh_mean = np.nanmean(np.where(np.isfinite(data["coh"]), data["coh"], np.nan), 0).astype("f4")
    valid = np.isfinite(mm).mean(0).astype("f4")
    pair_days = [(np.datetime64(_iso(b)) - np.datetime64(_iso(a))).astype(int) for a, b in pairs]
    np.savez_compressed(
        C.WORK / site / track / out_name,
        dates=np.array([_iso(d) for d in dates]), cum=cum.astype("f4"), vel=vel, vel_sig=sig, annual_amp=amp,
        rate12=np.full(vel.shape, np.nan, "f4"), rate24=np.full(vel.shape, np.nan, "f4"), n_triplets=ntrip,
        coh_mean=coh_mean, valid_share=valid,
        gaps=np.array([f"{_iso(a)}/{_iso(b)}" for a, b in breaks]),
        gap_ranges=np.array([[_iso(a), _iso(b)] for a, b in breaks]).reshape(-1, 2),
        n_pairs=len(pairs), pair_days=np.array(pair_days), pairs=np.array([f"{a}_{b}" for a, b in pairs]),
        tropo_mm_per_100m=slopes.astype("f4"), group=np.array(groups),
        iono_used=np.array([q["iono_used"] for q in data["qa"]]), phase_sign=sign,
        reference="terrain-relative: stable ground outside the zones + C.EXCLUDE_KM is 0 in every pair",
        made_by="stack.py (03)", synthetic=bool(meta.get("synthetic", False)))
    fin = np.isfinite(vel)
    stable = stable_mask(site, meta) & fin
    summary = dict(track=track, dates=len(dates), pairs=len(pairs), groups=len(set(groups)), triplets=ntrip,
                   pixels=float(fin.mean()), stable_median=float(np.median(vel[stable])),
                   stable_mad=float(1.4826 * np.median(np.abs(vel[stable] - np.median(vel[stable])))),
                   tropo=float(np.median(slopes)))
    print(f"{track}: {len(dates)} dates, {len(pairs)} pairs, {summary['groups']} group(s), {ntrip} triplets · "
          f"{summary['pixels']:.0%} pixels with a rate · stable ground {summary['stable_median']:+.1f} ± "
          f"{summary['stable_mad']:.1f} mm/yr (MAD) · troposphere removed, median {summary['tropo']:+.1f} mm per 100 m · "
          f"sign {sign:+d}")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    ap.add_argument("--track", help="only this track")
    ap.add_argument("--sign", type=int, choices=(-1, 1), default=PHASE_SIGN, help="phase sign (T3 tests both)")
    a = ap.parse_args()
    trs = [a.track] if a.track else C.tracks(a.site)
    if not trs:
        raise C.todo("02", f"no tracks under data/work/{a.site}/: run fetch.py first")
    for tr in trs:
        run(a.site, tr, a.sign, "ts.npz" if a.sign == PHASE_SIGN else f"ts_sign{a.sign:+d}.npz")


if __name__ == "__main__":
    C.run_cli(main)
