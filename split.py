# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""03 · InSAR analyst: ascending + descending calibrated rates → vertical and east–west.

Status: WORKING on real data (14 Nov 2026).

    python split.py ocnele_mari

Reads per track: meta.json, geom.npz (fetch.py), ts.npz (stack.py), cal.npz (calibrate.py; ts.npz if absent).
Writes data/work/<site>/up_east.npz (hand-off to 05 and 06): up, east, sig_up, sig_east (mm/yr) on the reference
track's grid, ref_track, window, note.

Per pixel solve [e_asc u_asc; e_desc u_desc] · [east; up] = [v_asc; v_desc].
- North is dropped: both looks are nearly blind to it (|n| ≈ 0.2); the page says so.
- Same months only (decision logged 14 Nov 2026, 21:30): 129A spans Nov 2025 to Oct 2026 with a gap, 094D only Jun to
  Oct 2026. Each track's rate is refitted here on its dates inside SUMMER (one line, no group offsets needed: every
  summer date is in one acquisition group), so both rates cover the same months.
- With one track only: up = LOS / u (assumes no horizontal motion) and the note says so.
- σ propagates through the 2×2 inverse from each track's line-fit σ, which assumes independent dates: a lower bound.
"""
from __future__ import annotations

import argparse

import common as C

SUMMER = ("2026-06-01", "2026-10-31")   # the window both NISAR tracks cover (094D 20 Jun to 18 Oct, 129A 23 Jun to 21 Oct)


def resample(src_meta: dict, arr, dst_meta: dict):
    """Nearest-neighbour sample of a src-grid array at the dst grid's pixel centres (different UTM zones allowed)."""
    import numpy as np
    X = dst_meta["x0"] + np.arange(dst_meta["nx"]) * dst_meta["dx"]
    Y = dst_meta["y0"] + np.arange(dst_meta["ny"]) * dst_meta["dy"]
    X, Y = np.meshgrid(X, Y)
    if src_meta["epsg"] != dst_meta["epsg"]:
        lon, lat = C.to_lonlat(dst_meta["epsg"], X, Y)
        X, Y = C.to_xy(src_meta["epsg"], lon, lat)
    j = np.rint((X - src_meta["x0"]) / src_meta["dx"]).astype(int)
    i = np.rint((Y - src_meta["y0"]) / src_meta["dy"]).astype(int)
    ok = (i >= 0) & (i < src_meta["ny"]) & (j >= 0) & (j < src_meta["nx"])
    out = np.full(X.shape + arr.shape[:-2], np.nan, "f4") if arr.ndim > 2 else np.full(X.shape, np.nan, "f4")
    src = np.moveaxis(arr, (-2, -1), (0, 1)) if arr.ndim > 2 else arr
    out[ok] = src[i[ok], j[ok]]
    return np.moveaxis(out, (0, 1), (-2, -1)) if arr.ndim > 2 else out


def solve_up_east(v_asc, e_asc, u_asc, s_asc, v_desc, e_desc, u_desc, s_desc):
    """2×2 solve per pixel → up, east, sig_up, sig_east."""
    import numpy as np
    det = e_asc * u_desc - u_asc * e_desc
    east = (u_desc * v_asc - u_asc * v_desc) / det
    up = (e_asc * v_desc - e_desc * v_asc) / det
    sig_east = np.sqrt((u_desc * s_asc) ** 2 + (u_asc * s_desc) ** 2) / np.abs(det)
    sig_up = np.sqrt((e_desc * s_asc) ** 2 + (e_asc * s_desc) ** 2) / np.abs(det)
    return up, east, sig_up, sig_east


def summer_rate(dates, cum):
    """Line through the dates inside SUMMER → (rate, σ lower bound) per pixel, mm/yr."""
    import numpy as np
    keep = [k for k, d in enumerate(dates) if SUMMER[0] <= d <= SUMMER[1]]
    t = C.years([dates[k] for k in keep])
    y = cum[keep].reshape(len(keep), -1)
    ok = np.isfinite(y).all(0)
    A = np.c_[t, np.ones_like(t)]
    c, *_ = np.linalg.lstsq(A, np.where(ok, y, 0), rcond=None)
    r = y - A @ c
    s = np.sqrt((r ** 2).sum(0) / (len(t) - 2) * np.linalg.inv(A.T @ A)[0, 0])
    rate = np.where(ok, c[0], np.nan).reshape(cum.shape[1:])
    return rate.astype("f4"), np.where(ok, s, np.nan).reshape(cum.shape[1:]).astype("f4"), [dates[k] for k in keep]


def load(site: str, track: str):
    import numpy as np
    d = C.WORK / site / track
    meta = C.load_json(d / "meta.json")
    geom = dict(np.load(d / "geom.npz"))
    ts = dict(np.load(d / "ts.npz"))
    cum = dict(np.load(d / "cal.npz"))["cum_cal"] if (d / "cal.npz").exists() else ts["cum"]
    rate, sig, used = summer_rate([str(x) for x in ts["dates"]], cum)
    return meta, geom, rate, sig, used, (d / "cal.npz").exists()


def run(site: str) -> None:
    import numpy as np
    trs = C.tracks(site)
    if not trs:
        raise C.todo("02", f"no tracks under data/work/{site}/: run fetch.py first")
    asc = [t for t in trs if t.endswith("A")]
    desc = [t for t in trs if t.endswith("D")]
    out = C.WORK / site / "up_east.npz"
    if not (asc and desc):
        t = trs[0]
        meta, geom, rate, sig, used, tied = load(site, t)
        up = rate / geom["los_u"]
        np.savez_compressed(out, up=up, east=np.full_like(up, np.nan), sig_up=sig / geom["los_u"],
                            sig_east=np.full_like(up, np.nan), ref_track=t, window=np.array(SUMMER),
                            note=f"One track only ({t}): up = LOS / u, assuming no horizontal motion.")
        print(f"{t} only: up = LOS/u, assumes no horizontal motion")
        return
    a, d = asc[0], desc[0]
    ma, ga, va, sa, ua, ta = load(site, a)
    md, gd, vd, sd, ud, td = load(site, d)
    rs = lambda x: resample(md, x, ma)
    up, east, sup, seast = solve_up_east(va, ga["los_e"], ga["los_u"], sa,
                                         rs(vd), rs(gd["los_e"]), rs(gd["los_u"]), rs(sd))
    note = (f"{a} and {d} rates refitted on their dates in {SUMMER[0]} to {SUMMER[1]} "
            f"({ua[0]} to {ua[-1]} and {ud[0]} to {ud[-1]}); north ignored (both looks nearly blind to it); "
            f"{'GNSS-tied (cal.npz)' if ta and td else 'terrain-relative (no cal.npz)'}; σ is a lower bound.")
    np.savez_compressed(out, up=up.astype("f4"), east=east.astype("f4"), sig_up=sup.astype("f4"),
                        sig_east=seast.astype("f4"), ref_track=a, window=np.array(SUMMER), note=note)
    fin = np.isfinite(up)
    print(f"up/east on the {a} grid: {fin.mean():.0%} of pixels · up median {np.nanmedian(up):+.1f} mm/yr, "
          f"σ_up median {np.nanmedian(sup):.1f} · east median {np.nanmedian(east):+.1f} mm/yr · {note}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    run(ap.parse_args().site)


if __name__ == "__main__":
    C.run_cli(main)
