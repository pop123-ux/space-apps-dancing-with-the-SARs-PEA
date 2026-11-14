# Owner: 05 · Validator (Paul)
# Exploration only (never imported). Run from anywhere:
#   python notebooks/05/z3_check.py <repo root> <folder with 029A.npz and 007D.npz>
# The grids come from sentinel1/assets (restore_grids.py, or join the .part files and check SHA256SUMS).
# Needs data/work/ocnele_mari/refs/egms_up.csv and egms_east.csv from egms_cut.py.
"""z3 investigation: EGMS 2020-2025 bowl vs Sentinel-1 2026 grids (read-only, scratch)."""
import sys
import numpy as np
import pandas as pd
from pyproj import Transformer

repo, grids = sys.argv[1], sys.argv[2]
sys.path.insert(0, repo)
import common as C  # noqa: E402

to_utm = Transformer.from_crs(4326, 32635, always_xy=True)
z3 = next(z for z in C.SITES["ocnele_mari"]["zones"] if z["id"] == "z3")
zx, zy = to_utm.transform(z3["lon"], z3["lat"])

up = pd.read_csv(f"{repo}/data/work/ocnele_mari/refs/egms_up.csv")
ea = pd.read_csv(f"{repo}/data/work/ocnele_mari/refs/egms_east.csv")
eg = up.merge(ea, on=["lon", "lat"], suffixes=("_up", "_e"))
eg["x"], eg["y"] = to_utm.transform(eg.lon.values, eg.lat.values)
eg["d_z3"] = np.hypot(eg.x - zx, eg.y - zy)

print(f"z3 centre {z3['lat']}, {z3['lon']}, radius {z3['r_m']} m")
hot = eg[eg.v_up <= -10].copy()
print(f"\nEGMS cells with Up <= -10 mm/yr: {len(hot)}")
print(f"  inside z3 circle: {(hot.d_z3 <= z3['r_m']).sum()}, within 1 km of z3: {(hot.d_z3 <= 1000).sum()}")
near = hot[hot.d_z3 <= 1500].sort_values("v_up")
cx, cy = near.x.mean(), near.y.mean()
clon, clat = Transformer.from_crs(32635, 4326, always_xy=True).transform(cx, cy)
print(f"  centroid of the fast cells within 1.5 km: {clat:.4f} N, {clon:.4f} E, "
      f"{np.hypot(cx - zx, cy - zy):.0f} m from the z3 centre")

for t in ["029A", "007D"]:
    z = np.load(f"{grids}/{t}.npz")
    xmin, ymin, xmax, ymax = z["bounds_utm"]
    rate, e, u, disp = z["rate_mm_yr"], z["e"], z["u"], z["displacement_mm"]
    ny, nx = rate.shape
    px = (xmax - xmin) / nx
    X = xmin + (np.arange(nx) + 0.5) * px
    Y = ymax - (np.arange(ny) + 0.5) * px
    XX, YY = np.meshgrid(X, Y)
    D = np.hypot(XX - zx, YY - zy)
    print(f"\n=== {t} ({px:.0f} m pixels, {len(z['dates'])} dates {z['dates'][0]}..{z['dates'][-1]})")
    for r0, r1 in [(0, 300), (300, 600), (600, 1000), (1000, 2000)]:
        m = (D >= r0) & (D < r1)
        ok = m & np.isfinite(rate)
        print(f"  ring {r0:4d}-{r1:4d} m: {m.sum():5d} px, valid {ok.sum():5d} ({100 * ok.sum() / m.sum():4.0f} %)"
              + (f", median rate {np.nanmedian(rate[ok]):6.1f} mm/yr" if ok.any() else ""))

    def sample(df):
        ix = np.clip(((df.x - xmin) / px).astype(int), 0, nx - 1)
        iy = np.clip(((ymax - df.y) / px).astype(int), 0, ny - 1)
        r = rate[iy, ix]
        exp = df.v_up.values * u[iy, ix] + df.v_e.values * e[iy, ix]
        return r, exp

    for label, sel in [("EGMS fast cells (Up <= -10) within 1.5 km of z3", eg[(eg.v_up <= -10) & (eg.d_z3 <= 1500)]),
                       ("EGMS stable cells (|Up| < 1.5) within 1.5-3 km of z3",
                        eg[(eg.v_up.abs() < 1.5) & (eg.d_z3.between(1500, 3000))])]:
        r, exp = sample(sel)
        ok = np.isfinite(r)
        print(f"  {label}: {len(sel)} cells, Sentinel-1 valid at {ok.sum()}")
        if ok.any():
            print(f"     S1 2026 LOS rate median {np.median(r[ok]):6.1f} mm/yr | EGMS-predicted LOS {np.median(exp[ok]):6.1f} mm/yr")
