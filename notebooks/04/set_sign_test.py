# Owner: 04 · Geodesist (Matei)
"""Exploration only (never imported). T3: which way does NISAR's phase point? Test it with solid Earth tides.

    python notebooks/04/set_sign_test.py [129A|094D|all] [--local]

Every GUNW carries `slantRangeSolidEarthTidesPhase` (radians) in its radarGrid cube: the tide signal in the product's
own phase convention, the layer one subtracts from `unwrappedPhase`. The tide itself is known physics: it moves the
ground by up to about 30 cm, predictably, from the Sun and Moon. So, per pair and at the town:
  1. model the tide displacement (ENU) at both acquisition times (IERS 2010 eq. 7.5, degree 2, Love numbers
     h2 = 0.6078, l2 = 0.0847; Sun and Moon from astropy);
  2. project the change onto the product's own LOS unit vector (target to sensor): d_los, mm, positive = towards;
  3. turn the product's tide phase into mm with our draft rule, mm = PHASE_SIGN · phase · λ/4π.
If PHASE_SIGN = -1 is right, (3) equals (2): slope +1 across pairs. If it is wrong, slope -1.
No ground motion, no atmosphere and no reference area are involved, so a slow site cannot hide the answer.

Reads the downloaded first 129A pair from data/raw/nisar/ (--local), or streams only the radar-grid layers of every
cataloged pair with the Earthdata token in .env (a few MB per pair). Writes notebooks/04/set_sign_test.json.
"""
import csv
import io
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data" / "work" / "ocnele_mari" / "r04"))
import numpy as np  # noqa: E402

import common as C  # noqa: E402

RG = "science/LSAR/GUNW/metadata/radarGrid"
ID = "science/LSAR/identification"
H2, L2 = 0.6078, 0.0847
GM = {"sun": 1.32712442099e20, "moon": 4.9028e12}
GM_E, R_E = 3.986004418e14, 6378136.6
PHASE_SIGN = -1


def body_itrs(name, when):
    from astropy.coordinates import ITRS, get_body
    from astropy.time import Time
    t = Time(when, scale="utc")
    b = get_body(name, t).transform_to(ITRS(obstime=t))
    return np.array([b.cartesian.x.to_value("m"), b.cartesian.y.to_value("m"), b.cartesian.z.to_value("m")])


def tide_enu(lat, lon, h, when):
    """Degree-2 solid Earth tide displacement (m) in ENU at one place and time."""
    la, lo = np.radians(lat), np.radians(lon)
    r = (R_E + h) * np.array([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])
    rh = r / np.linalg.norm(r)
    d = np.zeros(3)
    for name in ("sun", "moon"):
        Rj = body_itrs(name, when); Rn = np.linalg.norm(Rj); Rh = Rj / Rn
        k = GM[name] * np.linalg.norm(r) ** 4 / (GM_E * Rn ** 3)
        c = Rh @ rh
        d += k * (H2 * rh * (1.5 * c * c - 0.5) + 3 * L2 * c * (Rh - c * rh))
    E = np.array([-np.sin(lo), np.cos(lo), 0]); N = np.array([-np.sin(la) * np.cos(lo), -np.sin(la) * np.sin(lo), np.cos(la)])
    return np.array([d @ E, d @ N, d @ rh])


def open_h5(src):
    import h5py
    if str(src).startswith("http"):
        import r04_129a as R
        f = R.RangeFile(src, R.token(), block=1 << 18)
        return h5py.File(io.BufferedReader(f, 1 << 18), "r")
    return h5py.File(src, "r")


def one(src):
    s = C.SITES["ocnele_mari"]
    with open_h5(src) as h:
        rg = h[RG]
        epsg = int(rg["projection"][()]) if rg["projection"].shape == () else 32635
        cx, cy = C.to_xy(epsg, s["lon"], s["lat"])
        hts = rg["heightAboveEllipsoid"][:]; k = int(np.argmin(abs(hts - s["height_m"])))
        gx, gy = rg["xCoordinates"][:], rg["yCoordinates"][:]
        j, i = int(np.argmin(abs(gx - cx))), int(np.argmin(abs(gy - cy)))
        set_ph = float(rg["slantRangeSolidEarthTidesPhase"][k, i, j])
        le, ln = float(rg["losUnitVectorX"][k, i, j]), float(rg["losUnitVectorY"][k, i, j])
        t_ref = float(rg["referenceZeroDopplerAzimuthTime"][k, i, j]); t_sec = float(rg["secondaryZeroDopplerAzimuthTime"][k, i, j])
        u_ref = rg["referenceZeroDopplerAzimuthTime"].attrs["units"]; u_sec = rg["secondaryZeroDopplerAzimuthTime"].attrs["units"]
        wl = C.LIGHT / float(h["science/LSAR/GUNW/grids/frequencyA/centerFrequency"][()])
        track = int(h[f"{ID}/trackNumber"][()]); direction = h[f"{ID}/orbitPassDirection"][()].decode()
        tro = tropo_regression(h, rg, hts, gx, gy, epsg, when_key(u_ref, t_ref, u_sec, t_sec), track, direction)
    ep = lambda u: datetime.fromisoformat((u.decode() if isinstance(u, bytes) else u).split("since ")[1].strip()[:19])
    when_ref, when_sec = ep(u_ref) + timedelta(seconds=t_ref), ep(u_sec) + timedelta(seconds=t_sec)
    lu = float(np.sqrt(max(0.0, 1 - le * le - ln * ln))); l = np.array([le, ln, lu])
    d_ref, d_sec = tide_enu(s["lat"], s["lon"], float(hts[k]), when_ref), tide_enu(s["lat"], s["lon"], float(hts[k]), when_sec)
    model_mm = float(l @ (d_sec - d_ref)) * 1000          # towards the satellite, secondary minus reference
    product_mm = PHASE_SIGN * set_ph * wl * 1000 / (4 * np.pi)
    return dict(track=f"{track:03d}{direction[0]}", ref=when_ref.isoformat(timespec="seconds"), sec=when_sec.isoformat(timespec="seconds"),
                set_phase_rad=round(set_ph, 4), product_mm_draft_sign=round(product_mm, 2), model_mm=round(model_mm, 2),
                up_change_mm=round(float(d_sec[2] - d_ref[2]) * 1000, 2), **tro)


def when_key(u_ref, t_ref, u_sec, t_sec):
    ep = lambda u: datetime.fromisoformat((u.decode() if isinstance(u, bytes) else u).split("since ")[1].strip()[:19])
    a, b = ep(u_ref) + timedelta(seconds=t_ref), ep(u_sec) + timedelta(seconds=t_sec)
    return f"{a:%Y%m%d}_{b:%Y%m%d}"


def tropo_regression(h, rg, hts, gx, gy, epsg, key, track, direction):
    """Regress the stored window phase (iono removed) on NASA's troposphere layer at each pixel's DEM height.
    The layer is +4π/λ × range increase (isce3 troposphere.py). A slope near +1 means the phase also has
    positive = away, so mm towards = -phase·λ/4π (PHASE_SIGN = -1) is right; near -1 means it is wrong."""
    from scipy.interpolate import RegularGridInterpolator
    tdir = ROOT / "data" / "work" / "ocnele_mari" / f"{track:03d}{direction[0]}"
    f = tdir / f"{key}.npz"
    if not f.exists():
        return dict(tropo_slope=None, tropo_r=None, tropo_note=f"no window file {key}")
    meta = json.loads((tdir / "meta.json").read_text())
    dz = np.load(tdir / "dem.npz"); dem = dz["height"] if "height" in dz.files else dz["dem"]
    ph = np.load(f)["phase"].astype(float)
    X = meta["x0"] + meta["dx"] * np.arange(meta["nx"]); Y = meta["y0"] + meta["dy"] * np.arange(meta["ny"])
    sx = np.where((gx >= X.min() - 2000) & (gx <= X.max() + 2000))[0]; sy = np.where((gy <= Y.max() + 2000) & (gy >= Y.min() - 2000))[0]
    sl = (slice(None), slice(sy[0], sy[-1] + 1), slice(sx[0], sx[-1] + 1))
    cube = rg["hydrostaticTroposphericPhaseScreen"][sl] + rg["wetTroposphericPhaseScreen"][sl]
    yy, xx = gy[sy], gx[sx]
    if yy[0] > yy[-1]: yy, cube = yy[::-1], cube[:, ::-1]
    XX, YY = np.meshgrid(X, Y); ok = np.isfinite(dem) & np.isfinite(ph)
    pts = np.c_[np.clip(dem[ok], hts.min(), hts.max()), YY[ok], XX[ok]]
    T = RegularGridInterpolator((hts, yy, xx), cube, bounds_error=False, fill_value=None)(pts)
    p = ph[ok]; m = np.isfinite(T)
    tc, pc = T[m] - np.median(T[m]), p[m] - np.median(p[m])
    slope = float(tc @ pc / (tc @ tc)); r = float(np.corrcoef(tc, pc)[0, 1])
    return dict(tropo_slope=round(slope, 3), tropo_r=round(r, 3), tropo_spread_rad=round(float(np.std(tc)), 3), n_px=int(m.sum()))


def main():
    want = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "all"
    rows = []
    if "--local" in sys.argv:
        srcs = [str(p) for p in sorted((ROOT / "data" / "raw" / "nisar").glob("*.h5"))]
    else:
        cat = list(csv.DictReader(open(ROOT / "data" / "scenes" / "ocnele_mari_gunw.csv", encoding="utf-8")))
        srcs = [r["url"].strip() for r in cat if want in ("all", r["track"])]
    for src in srcs:
        try:
            r = one(src); rows.append(r)
            print(f"{r['track']} {r['ref'][:10]} -> {r['sec'][:10]}: product (draft sign) {r['product_mm_draft_sign']:+7.2f} mm · "
                  f"tide model {r['model_mm']:+7.2f} mm · up change {r['up_change_mm']:+7.1f} mm", flush=True)
        except Exception as e:
            print("FAILED", Path(src).name[:60], type(e).__name__, str(e)[:120], flush=True)
    out = {"method": __doc__.split("\n")[1], "rows": rows}
    for tr in sorted({r["track"] for r in rows}):
        p = np.array([r["product_mm_draft_sign"] for r in rows if r["track"] == tr]); m = np.array([r["model_mm"] for r in rows if r["track"] == tr])
        slope = float(p @ m / (m @ m)) if m @ m > 0 else float("nan")
        corr = float(np.corrcoef(p, m)[0, 1]) if len(p) > 2 else float("nan")
        out[tr] = dict(n=len(p), slope_product_over_model=round(slope, 3), r=round(corr, 3),
                       verdict="PHASE_SIGN -1 confirmed" if slope > 0.5 else "PHASE_SIGN -1 WRONG" if slope < -0.5 else "unclear")
        ts_ = [r["tropo_slope"] for r in rows if r["track"] == tr and r.get("tropo_slope") is not None]
        rs_ = [r["tropo_r"] for r in rows if r["track"] == tr and r.get("tropo_r") is not None]
        out[tr].update(tide_layer="opposite to the interferogram" if slope < -0.5 else "same as the interferogram" if slope > 0.5 else "unclear",
                       tropo_n=len(ts_), tropo_slope_median=round(float(np.median(ts_)), 3) if ts_ else None,
                       tropo_r_median=round(float(np.median(rs_)), 3) if rs_ else None,
                       tropo_pairs_positive=int(sum(s > 0 for s in ts_)),
                       phase_sign_verdict=("PHASE_SIGN -1 supported" if ts_ and np.median(ts_) > 0.3 else
                                           "PHASE_SIGN -1 contradicted" if ts_ and np.median(ts_) < -0.3 else "unclear"))
        out[tr]["verdict"] = out[tr].pop("verdict") + " (only if the tide layer shared the interferogram's convention; isce3 shows it does not)"
        print(f"{tr}: tide layer vs model slope {slope:+.3f} (r {corr:+.3f}); troposphere layer vs phase: median slope "
              f"{out[tr]['tropo_slope_median']}, median r {out[tr]['tropo_r_median']}, {out[tr]['tropo_pairs_positive']}/{len(ts_)} pairs positive "
              f"-> {out[tr]['phase_sign_verdict']}")
    (Path(__file__).with_suffix(".json")).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
