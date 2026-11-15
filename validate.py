# Owner: 05 · Validator (Paul)
"""05 · Validator: the checks the team did not tune. Nobody else edits this file.

Status: WORKING DRAFT, PROPOSED FOR 05 (14 Nov 2026). Written by the 02/03 session at Alexandru's request, as a pull
request for 05 to review, change and merge: the validator stays 05's. Thresholds are the advisor-kit ones below,
unchanged.

    python validate.py ocnele_mari

Reads (never writes) data/work/<site>/<track>/{meta.json, geom.npz, ts.npz, cal.npz} (02, 03, 04),
data/work/<site>/refs/stations.csv (04), products/<site>/{calib.json, series.json, manifest.json} (04, 06).
Writes products/<site>/ (file contracts in docs/build-spec.md):
    checks.json        [{id, status: pass|warn|fail|info, title, detail, value}]
    checks.md          the same, readable
    stations.geojson   per station: tracks {"nisar:<track>": {nisar, gnss, diff, tol}}, agree (true|false|null), reason,
                       nisar_up, gnss_up, source, dist_km, t_end

The checks (DRAFT thresholds from the advisor kit; 05 owns them):
1 sign      salt zones sink on every track: median LOS rate in the zones < −2 mm/yr, else the phase sign is wrong.
            (Rehearsal: 129A −4.6, 094D +27.5 mm/yr → not confirmed on real data.)
2 stations  held-out stations in each LOS: |NISAR − GNSS| ≤ max(C.TOL_FLOOR, 2σ combined). Old series (2018–2020) are
            flagged "assumes steady motion since". Stations can lie: check the monument (HAR1 mast) before blaming radar.
3 tie       robust scatter of the model tie < 6 mm/yr per pixel (rehearsal: 37 / 51 → WARN).
4 closure   12 + 12 against 24-day pairs over the same dates: ratio 0.8–1.2 (Ocnele Mari GUNW: 0 triplets → info).
5 gaps      dates no pair spans (129A: 18 Jan → 23 Jun 2026): listed, slider must show "no data" there.
6 egms      EGMS Ortho Up 2020–2024, stable ground: median |NISAR − EGMS| < 1.5 mm/yr; the bowl then vs now is reported,
            not judged (a difference is the story, not an error).
7 truth     synthetic site only: up bias < 1 mm/yr, zones within 15 %.
8 s1        NISAR against Sentinel-1 (D-004), per zone over the common window (C.COMMON_WINDOW), as zone minus outer
            reference band until the team decides how to compare the two radars: agree within the combined errors, disagree, or not testable (too few pixels).

Choices made in this draft (05 to confirm):
- Check 1 runs on every fitted track, exported or not (094D is held off the page because of this check).
- Check 1 also reports each zone against ground at the same height (±30 m) within 3 km, when the track has dem.npz.
  On 094D the far stable ground sits 100 m above the zones and the valley floor reads +15 to +25 mm/yr at every height
  below 300 m, so a far reference measures the valley, not the zones (docs/validation-log.md, 14 Nov 21:45). The
  pass/fail rule is unchanged; the height-matched numbers are reported beside it.
- Check 2 compares only tracks on the page; σ_GNSS is the published LOS-projected error. σ_NISAR is the robust spread
  of 7 × 7 box medians sampled over the tie pixels: what one station-sized box scatters by against the frame. The old
  σ (box scatter / √n) treated neighbouring pixels as independent and came out about ten times too small (2.7 against
  about 26 mm/yr on 129A), because the noise is correlated over kilometres.
- Checks 2 and 8 report warn, not pass or fail, when their tolerance is wider than TOL_DECISIVE (20 mm/yr): a check
  that cannot fail is not evidence, and a "fail" inside noise that large is not evidence either way.
- Check 8 pairs tracks by look geometry, not by direction (proposal for comparing the radars, 14 Nov 21:45): NISAR looks left and
  Sentinel-1 right, so NISAR 129A (ascending, east +0.62) sees east-west motion like Sentinel-1 007D (descending,
  east +0.64), not like 029A (east -0.64). With EGMS zone east rates of -4.1 to +4.9 mm/yr, pairing by direction put
  -5 to +6 mm/yr of geometry into the difference; pairing by geometry leaves under 0.1 mm/yr. NISAR is still scaled
  into Sentinel-1's line of sight by the ratio of the up components, which is now nearly exact.
"""
from __future__ import annotations

import argparse
import csv
import math

import common as C

STATUSES = ("pass", "warn", "fail", "info")
SIGN_MAX = -2.0          # mm/yr, check 1
TIE_MAX = 6.0            # mm/yr, check 3
EGMS_MAX = 1.5           # mm/yr, check 6
STATION_R_PX = 3         # pixels around a station (7 × 7 at 80 m)
S1_MIN_PX = 10           # pixels a zone needs on each satellite, check 8
TOL_DECISIVE = 20.0      # mm/yr: a wider tolerance cannot decide, so checks 2 and 8 report warn (draft choice)
S1_TOL_DECISIVE = TOL_DECISIVE
SAME_HEIGHT_M, LOCAL_BOX_PX = 30.0, 38   # check 1: same-height ground within ±30 m, in a box ±3 km around the zone
# Sentinel-1 track with the same east sensitivity as each NISAR track (left vs right looking), and its look vector:
# medians of the e and u grids in sentinel1/analysis/<track>.npz (14 Nov 2026). The north component is not in the S1 fit.
S1_PAIR = {"129A": "007D", "094D": "029A"}
S1_LOOK = {"029A": dict(e=-0.636, u=0.764), "007D": dict(e=0.640, u=0.760)}
ZONES = ("z1", "z2", "z3", "z4")


# ------------------------------------------------------------------------------------------------ helpers
def fitted_tracks(site):
    return [t for t in C.tracks(site) if (C.WORK / site / t / "ts.npz").exists()]


def load(site, track):
    import numpy as np
    d = C.WORK / site / track
    meta = C.load_json(d / "meta.json")
    ts = dict(np.load(d / "ts.npz"))
    geom = dict(np.load(d / "geom.npz"))
    cal = dict(np.load(d / "cal.npz")) if (d / "cal.npz").exists() else None
    return meta, ts, geom, cal


def zone_masks(site, meta):
    import export
    return export.nisar_zone_masks(C.SITES[site], meta)


def pick(meta: dict, arr, lon: float, lat: float, r_px: int = 2):
    """Median of arr within r_px pixels of a point, NaN outside the window. → (median, robust σ, n)."""
    import numpy as np
    x, y = C.to_xy(meta["epsg"], lon, lat)
    j = int(round((x - meta["x0"]) / meta["dx"]))
    i = int(round((y - meta["y0"]) / meta["dy"]))
    if not (0 <= i < meta["ny"] and 0 <= j < meta["nx"]):
        return math.nan, math.nan, 0
    a = arr[max(i - r_px, 0):i + r_px + 1, max(j - r_px, 0):j + r_px + 1]
    v = a[np.isfinite(a)]
    if not v.size:
        return math.nan, math.nan, 0
    med = float(np.median(v))
    return med, float(1.4826 * np.median(np.abs(v - med))), int(v.size)


def on_page(site):
    try:
        return sorted(C.load_json(C.PRODUCTS / site / "manifest.json")["sensors"]["nisar"].get("frames", {}))
    except (FileNotFoundError, KeyError):
        return []


# ------------------------------------------------------------------------------------------------ the checks
def check_sign(site, add):
    import numpy as np
    for t in fitted_tracks(site):
        meta, ts, _, _ = load(site, t)
        m = zone_masks(site, meta)
        v = np.concatenate([ts["vel"][m[z] & np.isfinite(ts["vel"])] for z in ZONES])
        r = float(np.median(v))
        local = same_height(site, t, ts["vel"], m)
        add(f"sign-{t}", "pass" if r < SIGN_MAX else "fail", f"Salt zones sink on NISAR {t}",
            f"Median line-of-sight rate over the zone pixels: {r:+.1f} mm/yr from {v.size} pixels "
            f"(needs < {SIGN_MAX:+.0f}; phase sign {int(ts['phase_sign']):+d}). "
            + ("" if r < SIGN_MAX else "Not a global sign error: unwrapping, the ECMWF weather model and NASA's own troposphere screens were all tested and none removes it (notebooks/03/t3_094d_checks.json); the track is shown flagged, for inspection only. ")
            + local, round(r, 2))


def same_height(site, track, vel, masks) -> str:
    """Each zone's median minus ground at the same height (±SAME_HEIGHT_M) within ±3 km, zones excluded."""
    import numpy as np
    f = C.WORK / site / track / "dem.npz"
    if not f.exists():
        return "No dem.npz for this track: the height-matched reading is not available."
    z = np.load(f)
    h = z["dem"] if "dem" in z.files else z["height"]   # fetch.py writes "dem"; the 04 stand-in wrote "height"
    anyzone = np.zeros(vel.shape, bool)
    for z in ZONES:
        anyzone |= masks[z]
    out = []
    for z in ZONES:
        zm = masks[z] & np.isfinite(vel)
        if not zm.any():
            continue
        ii, jj = np.nonzero(masks[z])
        box = np.zeros(vel.shape, bool)
        box[max(ii.min() - LOCAL_BOX_PX, 0):ii.max() + LOCAL_BOX_PX + 1,
            max(jj.min() - LOCAL_BOX_PX, 0):jj.max() + LOCAL_BOX_PX + 1] = True
        zh = float(np.nanmedian(h[masks[z]]))
        ref = box & ~anyzone & np.isfinite(vel) & (np.abs(h - zh) <= SAME_HEIGHT_M)
        if ref.sum() < 100:
            continue
        out.append(f"{z} {float(np.median(vel[zm]) - np.median(vel[ref])):+.1f}")
    return ("Against ground at the same height within 3 km (mm/yr): " + ", ".join(out) + ".") if out else ""


def read_stations(site):
    """Every station source with a full ENU rate, plus one inverse-variance mean per station name when it has several
    sources at the same monument (VLC1 NGL 2012-2018 and VLC2 Muntean 2019-2025 sit 0 m apart: "VLC (combined)")."""
    rows = list(csv.DictReader((C.WORK / site / "refs" / "stations.csv").open(encoding="utf-8")))
    full = [r for r in rows if not any(math.isnan(float(r[k])) for k in ("ve", "vn", "vu"))]
    keep = {}
    for r in full:                                   # one entry per station name: the newest full source
        if r["station"] not in keep or str(r["t_end"]) > str(keep[r["station"]]["t_end"]):
            keep[r["station"]] = r
    out = list(keep.values())
    groups = {}
    for r in out:
        groups.setdefault((round(float(r["lat"]), 3), round(float(r["lon"]), 3)), []).append(r)
    for g in groups.values():
        if len(g) < 2:
            continue
        m = dict(station=g[0]["station"][:3] + " (combined)", lat=g[0]["lat"], lon=g[0]["lon"],
                 source="Inverse-variance mean of " + " and ".join(f"{r['station']} ({r['source']}, to {str(r['t_end'])[:4]})" for r in g),
                 t_start=min(str(r["t_start"])[:4] for r in g), t_end=max(str(r["t_end"]) for r in g), combined=True)
        for c, sc in (("ve", "se"), ("vn", "sn"), ("vu", "su")):
            w = [1 / float(r[sc]) ** 2 for r in g]
            m[c] = sum(wi * float(r[c]) for wi, r in zip(w, g)) / sum(w)
            m[sc] = 1 / math.sqrt(sum(w))
        out.append(m)
    return out


def nearest_pick(meta, arr, lon, lat, r0=STATION_R_PX, r_max=12, need=10):
    """pick() with the box grown until it holds `need` coherent pixels (up to r_max pixels, about 1 km at 80 m)."""
    for r in range(r0, r_max + 1):
        v, sig, n = pick(meta, arr, lon, lat, r)
        if n >= need or (r == r0 and n):
            return v, sig, n, r
    return v, sig, n, r_max


def s1_grids():
    """Sentinel-1 July to October rate grids (029A, 007D) with their grid metadata and station-box σ."""
    import numpy as np
    import export
    out = {}
    for trk in ("029A", "007D"):
        z = export.load_grid(trk, "jul_oct")
        rate = z["rate_mm_yr"]
        xmin, ymin, xmax, ymax = z["bounds_utm"]
        ny, nx = rate.shape
        dx, dy = (xmax - xmin) / nx, (ymax - ymin) / ny
        meta = dict(epsg=32635, x0=xmin + dx / 2, y0=ymax - dy / 2, dx=dx, dy=-dy, nx=nx, ny=ny)
        out[trk] = dict(meta=meta, rate=rate, sig=box_sigma(dict(vel_cal=rate, tie=np.isfinite(rate)), r_px=5, step=11))
    return out


def check_stations(site, add):
    import numpy as np
    tracks = [t for t in on_page(site) if t in fitted_tracks(site)]
    feats, box_sig = [], {}
    s = C.SITES[site]
    try:
        s1 = s1_grids()
    except Exception:          # the Sentinel-1 grid chunks are not on this machine
        s1 = {}
    import refs
    band = refs.load_model(site, "euvem")(s["lon"], s["lat"])     # GNSS model at the town: Sentinel-1's terrain reference
    band = np.asarray(band, float).reshape(-1)[:3]
    for r in read_stations(site):
        lat, lon = float(r["lat"]), float(r["lon"])
        ve, vn, vu, se, sn, su = (float(r[k]) for k in ("ve", "vn", "vu", "se", "sn", "su"))
        per, agree_all, reasons, decisive = {}, [], [], []
        for t in tracks:
            meta, ts, geom, cal = load(site, t)
            if cal is None:
                continue
            if t not in box_sig:
                box_sig[t] = box_sigma(cal)
            v, sig, n, rpx = nearest_pick(meta, cal["vel_cal"], lon, lat)
            e, nn, u = (pick(meta, geom[k], lon, lat, 0)[0] for k in ("los_e", "los_n", "los_u"))
            if not n or not np.isfinite(e):
                reasons.append(f"NISAR {t}: no coherent pixel within {12 * 80} m")
                continue
            g = C.enu_to_los(e, nn, u, ve, vn, vu)
            sg = math.sqrt((e * se) ** 2 + (nn * sn) ** 2 + (u * su) ** 2)
            sn_ = box_sig[t] if math.isfinite(box_sig[t]) else sig / math.sqrt(n)
            tol = max(C.TOL_FLOOR, 2 * math.sqrt(sn_ ** 2 + sg ** 2))
            ok = abs(v - g) <= tol
            per[f"nisar:{t}"] = dict(nisar=round(v, 2), gnss=round(g, 2), diff=round(v - g, 2), tol=round(tol, 1), n_px=n,
                                     radius_m=int((2 * rpx + 1) * 40))
            agree_all.append(ok)
            decisive.append(tol <= TOL_DECISIVE)
            reasons.append(f"NISAR {t}: {v:+.1f} vs GNSS {g:+.1f} mm/yr (±{tol:.1f}, {n} px within {int((2 * rpx + 1) * 40)} m)")
        for trk, gr in s1.items():                   # Sentinel-1 is terrain-relative: compare with GNSS minus the model at the reference
            v, sig, n, rpx = nearest_pick(gr["meta"], gr["rate"], lon, lat, r0=5, r_max=25, need=15)
            if not n:
                continue
            lk = S1_LOOK[trk]
            g = C.enu_to_los(lk["e"], 0.0, lk["u"], ve - band[0], vn - band[1], vu - band[2])
            sg = math.sqrt((lk["e"] * se) ** 2 + (lk["u"] * su) ** 2)
            tol = max(C.TOL_FLOOR, 2 * math.sqrt((gr["sig"] if math.isfinite(gr["sig"]) else sig) ** 2 + sg ** 2))
            ok = abs(v - g) <= tol
            per[f"s1:{trk}"] = dict(radar=round(v, 2), gnss=round(g, 2), diff=round(v - g, 2), tol=round(tol, 1), n_px=n,
                                    radius_m=int((2 * rpx + 1) * 20))
            agree_all.append(ok)
            decisive.append(tol <= TOL_DECISIVE)
            reasons.append(f"Sentinel-1 {trk}: {v:+.1f} vs GNSS {g:+.1f} mm/yr relative to the terrain reference "
                           f"(±{tol:.1f}, {n} px within {int((2 * rpx + 1) * 20)} m)")
        agree = None if not agree_all else all(agree_all)
        dist = C.haversine_km(s["lat"], s["lon"], lat, lon)
        old = str(r["t_end"])[:4] < "2026"
        st = "info" if agree is None else ("warn" if not all(decisive) else "pass" if agree else "fail")
        period = f"{str(r.get('t_start', ''))[:4]} to {str(r['t_end'])[:4]}"
        feats.append(dict(type="Feature", geometry=dict(type="Point", coordinates=[round(lon, 5), round(lat, 5)]),
                          properties=dict(station=r["station"], source=r["source"], dist_km=round(dist, 1), period=period,
                                          combined=bool(r.get("combined")), tracks=per, agree=agree, status=st,
                                          reason="; ".join(reasons) or "No radar track covers this station",
                                          nisar_up=None, gnss_up=round(vu, 2), t_end=str(r["t_end"])[:4] if old else None)))
        add(f"station-{r['station'].replace(' ', '-').replace('(', '').replace(')', '')}", st,
            f"Held-out station {r['station']} against the radars",
            ("; ".join(reasons) or "No radar track covers this station")
            + (f". At least one tolerance is wider than {TOL_DECISIVE:.0f} mm/yr (a station-sized box of radar pixels "
               "scatters by that much on stable ground), so this neither confirms nor rejects the radar" if st == "warn" else "")
            + f". GNSS observation period {period}" + (": it assumes steady motion since." if old else ".")
            + f" Source: {r['source']}.", None if not per else round(max(abs(p['diff']) for p in per.values()), 2))
    C.save_json(C.PRODUCTS / site / "stations.geojson", dict(type="FeatureCollection", features=feats))


def box_sigma(cal, r_px: int = STATION_R_PX, step: int = 9) -> float:
    """Robust spread of (2r+1)² box medians over the tie pixels, on a regular sample: σ of one station-sized box."""
    import numpy as np
    v, tie = cal["vel_cal"], cal["tie"].astype(bool) & np.isfinite(cal["vel_cal"])
    meds = []
    for i in range(r_px, v.shape[0] - r_px, step):
        for j in range(r_px, v.shape[1] - r_px, step):
            b = v[i - r_px:i + r_px + 1, j - r_px:j + r_px + 1][tie[i - r_px:i + r_px + 1, j - r_px:j + r_px + 1]]
            if b.size >= (2 * r_px + 1) ** 2 // 2:
                meds.append(np.median(b))
    if len(meds) < 50:
        return math.nan
    m = np.asarray(meds)
    return float(1.4826 * np.median(np.abs(m - np.median(m))))


def zlabel(zid: str, site: str = "ocnele_mari") -> str:
    z = next((z for z in C.SITES[site]["zones"] if z["id"] == zid), {"id": zid})
    return C.zone_label(z)


def check_tie(site, add):
    calib = C.load_json(C.PRODUCTS / site / "calib.json")
    for e in calib.get("tracks", []):
        mad = e["residual_mad_mm_yr"]
        add(f"tie-{e['track']}", "pass" if mad < TIE_MAX else "warn", f"Tie scatter on NISAR {e['track']}",
            f"Robust scatter of NISAR minus {calib['model']} on {e['n_tie_pixels']} stable pixels: {mad:.1f} mm/yr per "
            f"pixel (target < {TIE_MAX:.0f}); {e['method']} correction {e['offset_mm_yr']:+.2f} mm/yr; model swap "
            f"against {e.get('swap_model')}: {e['swap_delta_mm_yr']:.2f} mm/yr (T8 < 1). Per-pixel rates are noise-"
            "dominated: read zones and areas, not single dots.", mad)
        add(f"swap-{e['track']}", "pass" if e["swap_delta_mm_yr"] < 1 else "warn", f"Model swap on NISAR {e['track']}",
            f"Changing the GNSS model to {e.get('swap_model')} moves the tied rates by {e['swap_delta_mm_yr']:.2f} mm/yr "
            "(needs < 1, T8).", e["swap_delta_mm_yr"])


def check_closure(site, add):
    for t in fitted_tracks(site):
        _, ts, _, _ = load(site, t)
        n = int(ts["n_triplets"])
        add(f"closure-{t}", "info", f"Closure on NISAR {t}",
            f"{n} triplets of two 12-day pairs and the 24-day pair over the same dates: the short-pair bias cannot be "
            "tested on this stack (the 24-day pairs replace missing 12-day pairs).", n)


def check_gaps(site, add):
    man = C.load_json(C.PRODUCTS / site / "manifest.json")
    frames = man["sensors"]["nisar"].get("frames", {})
    for t in fitted_tracks(site):
        _, ts, _, _ = load(site, t)
        gaps = [list(map(str, g)) for g in ts["gap_ranges"]]
        shown = frames.get(t, {}).get("gaps")
        if not gaps:
            add(f"gaps-{t}", "pass", f"No gaps on NISAR {t}", "Every date is connected to the others by pairs.", 0)
        elif shown is None:
            add(f"gaps-{t}", "info", f"Gaps on NISAR {t}", f"{gaps}; the track is not on the page.", len(gaps))
        else:
            ok = all(g in shown for g in gaps)
            add(f"gaps-{t}", "pass" if ok else "fail", f"Gaps shown on NISAR {t}",
                f"No pair spans {', '.join(f'{a} to {b}' for a, b in gaps)}; each acquisition group is referenced on its own "
                + ("and the page marks the gap." if ok else "but the page does not mark it."), len(gaps))


def check_egms(site, add):
    p = C.WORK / site / "refs" / "egms_up.csv"
    if not p.exists():
        e = C.load_json(C.PRODUCTS / site / "manifest.json").get("egms") or {}
        add("egms", "info", "EGMS stable ground",
            "The EGMS Ortho Up cut (refs/egms_up.csv, 05's egms_cut.py) is not on this machine, so NISAR minus EGMS was "
            f"not recomputed here. 05's reported result: {e.get('summary', 'not available')}.", None)
        return
    raise C.todo("05", "check 6 with refs/egms_up.csv on disk: NISAR up minus EGMS up on stable ground")


def check_truth(site, add):
    raise C.todo("05", "check 7: synthetic truth recovered (demo only; fetch.py --synthetic is still a stub)")


def check_sentinel1(site, add):
    import numpy as np
    series = C.load_json(C.PRODUCTS / site / "series.json")
    w0, w1 = C.COMMON_WINDOW
    for t in on_page(site):
        s1t = S1_PAIR[t]
        u_s1 = S1_LOOK[s1t]["u"]
        meta, ts, geom, cal = load(site, t)
        masks = zone_masks(site, meta)
        ctl = next(p for p in series if p["id"] == "outer_control")
        for z in ZONES:
            p = next(q for q in series if q["id"] == z)
            a, b = p["series"].get(f"nisar:{t}"), p["series"].get(f"s1:{s1t}")
            ca, cb = ctl["series"].get(f"nisar:{t}"), ctl["series"].get(f"s1:{s1t}")
            num = z[1:]
            if not (a and b and ca and cb) or min(a["n_pixels"], b["n_pixels"]) < S1_MIN_PX or u_s1 is None:
                why = "a satellite has no series here" if not (a and b) else f"fewer than {S1_MIN_PX} pixels" if (a and b) else ""
                add(f"agree-z{num}-{t}", "info", f"{zlabel(z, site)}: NISAR {t} against Sentinel-1 {s1t}",
                    f"Not testable: {why or 'no shared geometry'}.", None)
                continue

            def rate(e, c):
                d = [(x, y - c["mm"][c["dates"].index(x)]) for x, y in zip(e["dates"], e["mm"])
                     if w0 <= x <= w1 and x in c["dates"] and y is not None and c["mm"][c["dates"].index(x)] is not None]
                tt = C.years([x for x, _ in d]); yy = np.array([y for _, y in d])
                A = np.c_[tt, np.ones_like(tt)]
                cf, *_ = np.linalg.lstsq(A, yy, rcond=None)
                res = yy - A @ cf
                sig = math.sqrt((res ** 2).sum() / max(len(yy) - 2, 1) * np.linalg.inv(A.T @ A)[0, 0])
                return float(cf[0]), sig, len(yy)
            rn, sn, nn = rate(a, ca)
            rs, ss, ns = rate(b, cb)
            u_n = float(np.nanmean(geom["los_u"][masks[z]]))
            k = u_s1 / u_n
            diff = rn * k - rs
            tol = 2 * math.sqrt((sn * k) ** 2 + ss ** 2)
            status = "fail" if abs(diff) > tol else ("pass" if tol <= S1_TOL_DECISIVE else "warn")
            same = (rn < 0) == (rs < 0)
            add(f"agree-z{num}-{t}", status, f"{zlabel(z, site)}: NISAR {t} against Sentinel-1 {s1t}",
                f"Zone minus outer comparison area, {w0} to {w1}: NISAR {rn * k:+.1f} (scaled ×{k:.2f}; tracks paired by "
                f"east sensitivity, so east-west motion cancels) against Sentinel-1 {rs:+.1f} mm/yr; difference {diff:+.1f}, tolerance ±{tol:.1f} "
                f"(2σ, dates assumed independent: a lower bound); {nn} and {ns} dates, {a['n_pixels']} and {b['n_pixels']} px. "
                + (f"The tolerance is wider than {S1_TOL_DECISIVE:.0f} mm/yr, so agreeing is not evidence; "
                   if status == "warn" else "")
                + ("both satellites show the zone moving away from the satellite relative to its surroundings."
                   if same and rn < 0 else "the two satellites disagree in direction." if not same else "both show it moving toward the satellite."),
                round(diff, 2))


# ------------------------------------------------------------------------------------------------ run
def run(site: str) -> list[dict]:
    checks: list[dict] = []

    def add(id, status, title, detail, value=None):
        assert status in STATUSES, status
        checks.append(dict(id=id, status=status, title=title, detail=detail, value=value))

    for check in (check_sign, check_stations, check_tie, check_closure, check_gaps, check_egms, check_sentinel1):
        check(site, add)
    if C.SITES[site].get("synthetic"):
        check_truth(site, add)
    checks.insert(0, dict(id="validator-draft", status="info", title="Validator draft, pending 05's review",
                          detail="These checks were written by the 02/03 session at the team's request and wait for "
                                 "the validator (05) to review them. Thresholds are the advisor kit's, unchanged.",
                          value=None))
    C.save_json(C.PRODUCTS / site / "checks.json", checks)
    icon = {"pass": "✔", "warn": "!", "fail": "✘", "info": "·"}
    md = ["# Checks", "", f"Site: {site}. Written by `validate.py`; thresholds in its docstring.", ""]
    md += [f"- {icon[c['status']]} **{c['title']}** ({c['status']}): {c['detail']}" for c in checks]
    (C.PRODUCTS / site / "checks.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    for c in checks:
        print(f"{icon[c['status']]} {c['id']}: {c['title']}" + (f" · {c['value']}" if c["value"] is not None else ""))
    n = {k: sum(c["status"] == k for c in checks) for k in STATUSES}
    print(f"{site}: {n['pass']} pass · {n['warn']} warn · {n['fail']} fail · {n['info']} info")
    return checks


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    run(ap.parse_args().site)


if __name__ == "__main__":
    C.run_cli(main)
