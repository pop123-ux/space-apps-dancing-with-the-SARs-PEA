# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Exploration only (never imported). Why do the zones read +23.5 mm/yr on NISAR 094D (T3 failed)? The predeclared
order: unwrapping, then atmosphere (prompts/early-tests.md, T3).

    python notebooks/03/t3_094d_checks.py

Each check reruns the 094D stack in memory (stack.py functions, sign -1 unchanged) and reports the pooled zone-median
LOS rate, Zone 4 and the outer ring:
  baseline            as stack.py
  per-pair zone jump  zone median minus the stable-ground median, per pair (a 2π error is about 122 mm)
  drop one pair       each pair removed in turn (one date driving the rate shows up here)
  local reference     zones minus a ring 1 to 3 km from the zone edges, per pair, instead of the far stable ground
  weather model       ECMWF IFS stratified delay at 094D's acquisition time (04:30 UTC) removed per pair (tropo.py)
Writes notebooks/03/t3_094d_checks.json.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "sentinel1" / "scripts"))

import numpy as np  # noqa: E402

import common as C  # noqa: E402
import export  # noqa: E402
import stack  # noqa: E402

SITE, TRACK = "ocnele_mari", "094D"


def rate_of(pairs, mm, masks):
    dates = sorted({d for p in pairs for d in p})
    groups = stack.groups_of(pairs, dates)
    cum = stack.invert(pairs, dates, mm, groups)
    vel, _, _ = stack.fit_rate(dates, cum, groups)
    zones = np.concatenate([vel[masks[z] & np.isfinite(vel)] for z in ("z1", "z2", "z3", "z4")])
    z4 = vel[masks["z4"] & np.isfinite(vel)]
    ring = vel[masks["outer_control"] & np.isfinite(vel)]
    f = lambda a: round(float(np.median(a)), 2) if a.size else None
    return dict(zones=f(zones), z4=f(z4), outer=f(ring), n_zone_px=int(zones.size))


def main():
    meta, pairs, data, dem = stack.load_pairs(SITE, TRACK)
    mm, slopes = stack.to_mm_and_clean(SITE, meta, data, dem)
    masks = export.nisar_zone_masks(C.SITES[SITE], meta)
    stable = stack.stable_mask(SITE, meta)
    X = meta["x0"] + np.arange(meta["nx"]) * meta["dx"]; Y = meta["y0"] + np.arange(meta["ny"]) * meta["dy"]
    X, Y = np.meshgrid(X, Y)
    off = np.min([np.hypot(X - C.to_xy(meta["epsg"], z["lon"], z["lat"])[0], Y - C.to_xy(meta["epsg"], z["lon"], z["lat"])[1]) - z["r_m"]
                  for z in C.SITES[SITE]["zones"]], axis=0)
    near = (off >= 1000) & (off <= 3000)
    zone_any = masks["z1"] | masks["z2"] | masks["z3"] | masks["z4"]
    out = {"baseline": rate_of(pairs, mm, masks)}

    out["per_pair_zone_minus_stable_mm"] = {
        f"{a}_{b}": dict(zone_minus_stable=round(float(np.nanmedian(mm[k][zone_any]) - np.nanmedian(mm[k][stable])), 2),
                         zone_minus_local=round(float(np.nanmedian(mm[k][zone_any]) - np.nanmedian(mm[k][near])), 2),
                         zone_px=int(np.isfinite(mm[k][zone_any]).sum()), coh_zone=round(float(np.nanmedian(data["coh"][k][zone_any])), 2),
                         iono_std=round(float(data["qa"][k]["iono_std"]), 2))
        for k, (a, b) in enumerate(pairs)}

    out["drop_one_pair"] = {}
    for k in range(len(pairs)):
        keep = [i for i in range(len(pairs)) if i != k]
        out["drop_one_pair"][f"{pairs[k][0]}_{pairs[k][1]}"] = rate_of([pairs[i] for i in keep], mm[keep], masks)

    mm_local = mm.copy()
    for k in range(len(mm)):
        mm_local[k] = mm[k] - np.nanmedian(mm[k][near])
    out["local_reference_1_to_3_km"] = rate_of(pairs, mm_local, masks)

    import tropo
    days = sorted({d for p in pairs for d in p})
    iso = lambda d: f"{d[:4]}-{d[4:6]}-{d[6:]}"
    hourly = tropo.fetch(iso(days[0]), iso(days[-1]))
    hour = 4 + 30 / 60                         # 094D acquisitions at about 04:30 UTC (granule names, T0430..)
    ztd = {d: tropo.ztd_profile(tropo.day_slice(hourly, iso(d)), hour) for d in days}
    inc = np.radians(np.load(C.WORK / SITE / TRACK / "geom.npz")["incidence"])
    raw = stack.PHASE_SIGN * data["phase"] * meta["wavelength"] / (4 * np.pi) * 1000.0
    raw = np.where(data["coh"] >= C.MIN_COH, raw, np.nan)
    for k, (a, b) in enumerate(pairs):
        dz = np.interp(dem, tropo.HEIGHTS, ztd[b]) - np.interp(dem, tropo.HEIGHTS, ztd[a])
        raw[k] = raw[k] + dz / np.cos(inc)       # a delay reads as motion away (negative): add it back
    data_wm = dict(data, phase=raw / (stack.PHASE_SIGN * meta["wavelength"] / (4 * np.pi) * 1000.0))
    mm_wm, _ = stack.to_mm_and_clean(SITE, meta, data_wm, None)   # weather model instead of the fitted slope
    out["weather_model_no_fitted_slope"] = rate_of(pairs, mm_wm, masks)
    mm_wm2, _ = stack.to_mm_and_clean(SITE, meta, data_wm, dem)
    out["weather_model_plus_fitted_slope"] = rate_of(pairs, mm_wm2, masks)

    hz = np.isfinite(dem) & stable
    out["elevation"] = dict(zone_median_m=round(float(np.nanmedian(dem[zone_any])), 1),
                            stable_median_m=round(float(np.nanmedian(dem[hz])), 1),
                            fitted_slopes_mm_per_100m=[round(float(s), 2) for s in slopes])
    (ROOT / "notebooks" / "03" / "t3_094d_checks.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "per_pair_zone_minus_stable_mm"}, indent=1))
    print("per pair:", json.dumps(out["per_pair_zone_minus_stable_mm"]))


if __name__ == "__main__":
    main()
