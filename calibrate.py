# Owner: 04 · Geodesist (Matei)
"""04 · Geodesist: tie each track to the GNSS velocity model, the way EGMS calibrates its own product.

Status: WORKING on a synthetic track (known offset and plane recovered); waits for real
meta.json / geom.npz (02) and ts.npz (03).

    python calibrate.py ocnele_mari                  # tie to EuVeM2022; model swap against EGMS if model_egms.csv exists,
                                                     # otherwise against a rigid Eurasian plate (zero velocity)
    python calibrate.py ocnele_mari --model egms     # tie to the EGMS GNSS model (refs/model_egms.csv, same columns)
    python calibrate.py ocnele_mari --plot           # also write <track>/tie.png: NISAR − model on the tie pixels

Reads per track: meta.json, geom.npz (fetch.py), ts.npz (stack.py); refs/ (refs.py).
Writes per track data/work/<site>/<track>/cal.npz (vel_cal, cum_cal, model_los, tie, correction) and
products/<site>/calib.json (file contracts in docs/build-spec.md):
    {"model": "...", "tracks": [{track, direction, method: offset|plane, offset_mm_yr, slope_east_mm_yr_per_10km,
     slope_north_mm_yr_per_10km, n_tie_pixels, residual_std_mm_yr, residual_mad_mm_yr, model_los_mean_mm_yr,
     swap_delta_mm_yr}]}

The tie (build spec, "Tie and checks"):
- NISAR − model(LOS) on pixels that are coherent (≥ C.TIE_MIN_COH), outside the salt zones + C.EXCLUDE_KM and more than
  C.STATION_HOLDOUT_M from any station (stations are held out for validate.py).
- One offset, or a plane if it cuts the scatter (standard deviation of the inlier residuals) by more than 10 %;
  3σ outliers removed twice in each fit.
- offset_mm_yr is the fitted correction at the window centre; slopes are mm/yr per 10 km towards east and north.
- The correction is subtracted: vel_cal = vel − correction, cum_cal = cum − correction · (t − t_first of the date's
  group). ts.npz `group` (one per date) marks acquisition groups that no pair connects; each is referenced on its own.
- The model is a 0.1° grid: it fixes the frame-wide level and slopes only. It says nothing about a 2 km salt bowl.
- A plane hints at residual ionosphere: compare runs with and without the ionosphere layer.
- Model swap (O-06): swap_delta_mm_yr is the median |vel_cal(model) − vel_cal(second model)| on the tie pixels.
  T8 passes when it is under 1 mm/yr.
- Grid: pixel (i, j) is taken at x0 + j·dx, y0 + i·dy. If x0, y0 are the corner, the error is half a pixel (40 m), far
  below the 1 km and 3 km exclusion distances.
- Rehearsal numbers to beat: offsets −8.8 (094D) / −6.0 (129A) mm/yr, robust scatter 51 / 37 mm/yr.
"""
from __future__ import annotations

import argparse

import common as C

PLANE_GAIN = 0.10      # a plane must cut the scatter by more than this share
CLIP_SIGMA = 3.0       # outlier cut, in standard deviations
CLIP_ROUNDS = 2        # outlier passes per fit
MODELS = ["euvem", "egms", "plate"]


# ----------------------------------------------------------------------------------------------------------- inputs
def load_track(site: str, track: str):
    """→ meta, geom (los_e, los_n, los_u), ts (vel, cum, dates, coh_mean) for one track."""
    import numpy as np
    d = C.WORK / site / track
    meta = C.load_json(d / "meta.json")
    for f in ("geom.npz", "ts.npz"):
        if not (d / f).exists():
            who = "02 (fetch.py)" if f == "geom.npz" else "03 (stack.py)"
            raise C.todo("02" if f == "geom.npz" else "03", f"{d / f} is missing: {who} writes it")
    geom = dict(np.load(d / "geom.npz"))
    ts = dict(np.load(d / "ts.npz", allow_pickle=True))
    return meta, geom, ts


def pixel_xy(meta):
    """UTM coordinates (m) of every pixel of the window grid, shape (ny, nx)."""
    import numpy as np
    x = meta["x0"] + np.arange(meta["nx"]) * meta["dx"]
    y = meta["y0"] + np.arange(meta["ny"]) * meta["dy"]
    return np.meshgrid(x, y)


def model_velocity(site: str, model: str, lon, lat):
    """(ve, vn, vu) of the model at every pixel, shape (..., 3), Eurasia-fixed mm/yr."""
    import numpy as np
    if model == "plate":            # rigid Eurasian plate: nothing moves in a Eurasia-fixed frame
        return np.zeros(np.shape(lon) + (3,))
    import refs
    return refs.load_model(site, model)(lon, lat)


def model_to_los(site: str, track: str, model: str, meta=None, geom=None):
    """Sample the velocity model at every pixel and project (ve, vn, vu) onto the track's LOS (C.enu_to_los)."""
    if meta is None:
        meta, geom, _ = load_track(site, track)
    X, Y = pixel_xy(meta)
    lon, lat = C.to_lonlat(meta["epsg"], X, Y)
    v = model_velocity(site, model, lon, lat)
    return C.enu_to_los(geom["los_e"], geom["los_n"], geom["los_u"], v[..., 0], v[..., 1], v[..., 2])


# --------------------------------------------------------------------------------------------------------- the mask
def tie_mask(site: str, track: str, stations: list[dict], meta=None, coh=None):
    """Coherent stable pixels away from the salt zones and the stations. → (mask, counts of what each rule removed)."""
    import numpy as np
    if meta is None:
        meta, _, ts = load_track(site, track)
        coh = ts["coh_mean"]
    X, Y = pixel_xy(meta)
    keep = np.isfinite(coh) & (coh >= C.TIE_MIN_COH)
    why = {"low_coherence": int((~keep).sum())}
    near_zone = np.zeros_like(keep)
    for z in C.SITES[site]["zones"]:
        zx, zy = C.to_xy(meta["epsg"], z["lon"], z["lat"])
        near_zone |= np.hypot(X - zx, Y - zy) <= z["r_m"] + C.EXCLUDE_KM * 1000
    near_station = np.zeros_like(keep)
    for s in stations:
        if np.isfinite(s["lat"]) and np.isfinite(s["lon"]):
            sx, sy = C.to_xy(meta["epsg"], s["lon"], s["lat"])
            near_station |= np.hypot(X - sx, Y - sy) <= C.STATION_HOLDOUT_M
    why["salt_zones"] = int((keep & near_zone).sum())
    why["stations"] = int((keep & ~near_zone & near_station).sum())
    return keep & ~near_zone & ~near_station, why


# ---------------------------------------------------------------------------------------------------------- the fit
def _clipped_lstsq(A, r):
    """Least squares with CLIP_ROUNDS passes of CLIP_SIGMA rejection. → coefficients, inlier mask."""
    import numpy as np
    inl = np.ones(len(r), bool)
    c = np.linalg.lstsq(A, r, rcond=None)[0]
    for _ in range(CLIP_ROUNDS):
        res = r - A @ c
        s = res[inl].std()
        inl = np.abs(res - res[inl].mean()) <= CLIP_SIGMA * s
        c = np.linalg.lstsq(A[inl], r[inl], rcond=None)[0]
    return c, inl


def fit_tie(residual, mask, X, Y, xc, yc):
    """Offset or plane fit with outlier rejection on NISAR − model.
    → dict(method, coef [offset, slope_e, slope_n] in mm/yr and mm/yr per 10 km, inliers, std, mad), correction grid."""
    import numpy as np
    r = residual[mask]
    if r.size < 100:
        raise ValueError(f"only {r.size} tie pixels: too few for a tie (check coherence and the mask)")
    xe, yn = (X[mask] - xc) / 1e4, (Y[mask] - yc) / 1e4
    fits = {}
    for method, A in (("offset", np.ones((r.size, 1))), ("plane", np.c_[np.ones(r.size), xe, yn])):
        c, inl = _clipped_lstsq(A, r)
        res = (r - A @ c)[inl]
        fits[method] = dict(coef=np.r_[c, np.zeros(3 - len(c))], inliers=inl, std=float(res.std()),
                            mad=float(1.4826 * np.median(np.abs(res - np.median(res)))))
    use = "plane" if fits["plane"]["std"] < (1 - PLANE_GAIN) * fits["offset"]["std"] else "offset"
    f = dict(fits[use], method=use, std_offset=fits["offset"]["std"], std_plane=fits["plane"]["std"])
    c = f["coef"]
    correction = c[0] + c[1] * (X - xc) / 1e4 + c[2] * (Y - yc) / 1e4
    return f, correction


# ---------------------------------------------------------------------------------------------------------- per track
def tie_track(site, track, model, meta, geom, ts, stations):
    """One tie → (fit, correction, model_los, tie mask, why)."""
    import numpy as np
    X, Y = pixel_xy(meta)
    xc, yc = C.to_xy(meta["epsg"], C.SITES[site]["lon"], C.SITES[site]["lat"])
    mlos = model_to_los(site, track, model, meta, geom)
    tie, why = tie_mask(site, track, stations, meta, ts["coh_mean"])
    tie &= np.isfinite(ts["vel"]) & np.isfinite(mlos)
    fit, corr = fit_tie(ts["vel"] - mlos, tie, X, Y, xc, yc)
    used = np.zeros_like(tie)
    used[tie] = fit["inliers"]
    return fit, corr, mlos, used, why


def second_model(site: str, model: str) -> str:
    """The model to swap against: EGMS if its CSV exists (O-06), else a rigid plate; EuVeM2022 when tying to another."""
    if model != "euvem":
        return "euvem"
    return "egms" if (C.WORK / site / "refs" / "model_egms.csv").exists() else "plate"


def run(site: str, track: str, model: str, plot: bool = False) -> dict:
    import numpy as np
    import refs
    meta, geom, ts = load_track(site, track)
    stations = refs.load_stations(site)
    fit, corr, mlos, tie, why = tie_track(site, track, model, meta, geom, ts, stations)
    vel_cal = ts["vel"] - corr
    t = C.years([str(d)[:10] if "-" in str(d) else f"{str(d)[:4]}-{str(d)[4:6]}-{str(d)[6:8]}" for d in ts["dates"]])
    grp = np.asarray(ts["group"]) if "group" in ts else np.zeros(len(t), int)
    t_first = np.array([t[grp == g].min() for g in grp])   # each acquisition group starts at its own zero
    cum_cal = ts["cum"] - corr[None] * (t - t_first)[:, None, None]

    alt = second_model(site, model)
    fit2, corr2, _, _, _ = tie_track(site, track, alt, meta, geom, ts, stations)
    swap = float(np.median(np.abs((ts["vel"] - corr) - (ts["vel"] - corr2))[tie]))

    d = C.WORK / site / track
    np.savez_compressed(d / "cal.npz", vel_cal=vel_cal.astype("f4"), cum_cal=cum_cal.astype("f4"),
                        model_los=mlos.astype("f4"), tie=tie, correction=corr.astype("f4"),
                        model=model, swap_model=alt, synthetic=bool(meta.get("synthetic", False)))
    if plot:
        plot_tie(d / "tie.png", f"{track} · {model}", ts["vel"] - mlos, tie, fit)
    c = fit["coef"]
    entry = dict(sensor="nisar", track=track, direction=meta.get("direction", ""), method=fit["method"],
                 offset_mm_yr=round(float(c[0]), 2), slope_east_mm_yr_per_10km=round(float(c[1]), 3),
                 slope_north_mm_yr_per_10km=round(float(c[2]), 3), n_tie_pixels=int(tie.sum()),
                 residual_std_mm_yr=round(fit["std"], 2), residual_mad_mm_yr=round(fit["mad"], 2),
                 model_los_mean_mm_yr=round(float(np.mean(mlos[tie])), 2),
                 swap_delta_mm_yr=round(swap, 3), swap_model=alt,
                 swap_offset_mm_yr=round(float(fit2["coef"][0]), 2),
                 frame="Eurasia-fixed (EuVeM2022: horizontals ETRF2000, up IGS14)" if model == "euvem" else model,
                 dates=[str(x) for x in ts["dates"]],
                 gaps=[list(map(str, g)) for g in ts["gap_ranges"]] if "gap_ranges" in ts else [],
                 ts_made_by=str(ts["made_by"]) if "made_by" in ts else "stack.py",
                 phase_sign=int(ts["phase_sign"]) if "phase_sign" in ts else None)
    print(f"{track}: {fit['method']} {c[0]:+.2f} mm/yr (east {c[1]:+.2f}, north {c[2]:+.2f} per 10 km) · "
          f"{entry['n_tie_pixels']} tie pixels · scatter {fit['std']:.1f} (MAD {fit['mad']:.1f}) mm/yr · "
          f"plane/offset scatter {fit['std_plane']:.1f}/{fit['std_offset']:.1f} · swap vs {alt}: {swap:.2f} mm/yr · "
          f"removed: {why}")
    return entry


def plot_tie(path, track, residual, tie, fit) -> None:
    """Map and histogram of NISAR − model on the tie pixels (a check for 04, not a product)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    r = np.where(tie, residual, np.nan)
    v = np.nanpercentile(np.abs(r), 98)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    im = ax[0].imshow(r, cmap="RdBu", vmin=-v, vmax=v)
    fig.colorbar(im, ax=ax[0], label="NISAR − model, LOS (mm/yr)")
    ax[0].set_title(f"{track}: tie pixels")
    ax[1].hist(residual[tie], bins=80, color="0.4")
    ax[1].axvline(fit["coef"][0], color="k", label=f"{fit['method']} {fit['coef'][0]:+.1f} mm/yr")
    ax[1].set_xlabel("NISAR − model, LOS (mm/yr)")
    ax[1].legend()
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    print(f"  plot: {path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    ap.add_argument("--model", default="euvem", choices=MODELS, help="velocity model for the tie")
    ap.add_argument("--plot", action="store_true", help="write <track>/tie.png")
    ap.add_argument("--track", help="tie only this track; other tracks' entries in calib.json are kept")
    a = ap.parse_args()
    trs = [a.track] if a.track else C.tracks(a.site)
    if not trs:
        raise C.todo("02", f"no tracks under data/work/{a.site}/: run fetch.py first")
    entries = [run(a.site, tr, a.model, a.plot) for tr in trs]
    p = C.PRODUCTS / a.site / "calib.json"
    if a.track and p.exists():   # keep the other tracks' ties if they used the same model
        old = C.load_json(p)
        if old.get("model") == a.model:
            entries = [e for e in old.get("tracks", []) if e.get("track") not in trs] + entries
    out = dict(model=a.model, tracks=sorted(entries, key=lambda e: e["track"]))
    if C.SITES[a.site].get("synthetic"):
        out.update(synthetic=True, note="Simulated, not data")
    C.save_json(C.PRODUCTS / a.site / "calib.json", out)


if __name__ == "__main__":
    C.run_cli(main)
