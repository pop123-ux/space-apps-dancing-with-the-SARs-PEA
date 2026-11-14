# Owner: 05 · Validator (Paul)
"""05 · Validator: cut the EGMS L3 Ortho tile to the analysis window, and report the bowl's 2020 to 2025 history.

    python egms_cut.py ocnele_mari
    python egms_cut.py ocnele_mari --zips data/egms --release 2020_2025_1

Input (never committed, free EGMS login): the two Ortho zips of tile E54N25 from https://egms.land.copernicus.eu/,
saved by hand in data/egms/ (data/README.md lets 05 write the EGMS file):
    EGMS_L3_E54N25_100km_U_<release>.zip     vertical (Up), mm/yr, sinking is negative
    EGMS_L3_E54N25_100km_E_<release>.zip     east-west, mm/yr, east is positive

Writes:
    data/work/<site>/refs/egms_up.csv     lon, lat, v (contract in docs/build-spec.md), read by 04 and validate.py check 6
    data/work/<site>/refs/egms_east.csv   lon, lat, v (same layout, for the bowl's horizontal motion)
    data/work/<site>/refs/egms_meta.json  release, period, epochs, window, and the per-zone numbers printed below
    docs/figures/05_egms_up_rate.png      Up rate map of the inner 10 km with the zones
    docs/figures/05_egms_zone_history.png median cumulative Up per zone and on stable ground

EGMS points are 100 m cells in ETRS89-LAEA (EPSG 3035). Zone numbers are medians of the cells whose centre lies inside
the zone circle from common.py; "stable" is the window outside the zones plus C.EXCLUDE_KM. This script reports, it
does not judge: the checks live in validate.py.
"""
from __future__ import annotations

import argparse

import common as C

TILE = "E54N25"
EGMS_EPSG = 3035


def load(zips, component: str, release: str):
    import zipfile

    import pandas as pd
    name = f"EGMS_L3_{TILE}_100km_{component}_{release}"
    path = zips / f"{name}.zip"
    if not path.exists():
        raise SystemExit(f"missing {path}: download it from EGMS Explorer (Ortho, tile {TILE}) into {zips}")
    with zipfile.ZipFile(path) as z, z.open(f"{name}.csv") as f:
        return pd.read_csv(f)


def cut(df, site: dict):
    """Keep the cells inside the square analysis window; add lon, lat and the distance to the window centre."""
    import numpy as np
    df = df.copy()
    lon, lat = C.to_lonlat(EGMS_EPSG, df.easting.to_numpy(), df.northing.to_numpy())
    df = df.assign(lon=lon, lat=lat)
    half = site["half_km"]
    dy = (df.lat - site["lat"]) * 111.32
    dx = (df.lon - site["lon"]) * 111.32 * np.cos(np.radians(site["lat"]))
    return df[(dx.abs() <= half) & (dy.abs() <= half)].assign(dx_km=dx, dy_km=dy).copy()


def zone_masks(df, site: dict):
    import numpy as np
    masks, near = {}, np.zeros(len(df), bool)
    for z in site["zones"]:
        d_m = [C.haversine_km(z["lat"], z["lon"], a, b) * 1000 for a, b in zip(df.lat, df.lon)]
        d_m = np.array(d_m)
        masks[z["id"]] = d_m <= z["r_m"]
        near |= d_m <= z["r_m"] + C.EXCLUDE_KM * 1000
    masks["stable"] = ~near
    return masks


def dist_m(df, lat: float, lon: float):
    """Distance in metres from (lat, lon) to every cell (equirectangular; fine inside a 50 km window)."""
    import numpy as np
    return 111_320 * np.hypot(df.lat - lat, (df.lon - lon) * np.cos(np.radians(lat))).to_numpy()


def station_positions(site_name: str) -> dict:
    """Station (lat, lon): refs/stations.csv when 04 has written it, else common.PUBLISHED (VLC1 shares VLC2's spot)."""
    import csv
    p = C.WORK / site_name / "refs" / "stations.csv"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return {r["station"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(f)}
    pos = {k: (v[0], v[1]) for k, v in C.PUBLISHED.items()}
    pos.setdefault("VLC1", pos.get("VLC2"))
    return pos


def stable_ground(up, site: dict, site_name: str) -> dict:
    """Does EGMS agree that the ground the tie assumes stable is stable? Two areas from docs/build-spec.md:
    tie area = outside the zones plus C.EXCLUDE_KM and more than C.STATION_HOLDOUT_M from any station;
    check-6 set = EGMS points with |v| < 1.5 mm/yr outside the zones plus 500 m."""
    import numpy as np
    zone_d = np.min([dist_m(up, z["lat"], z["lon"]) - z["r_m"] for z in site["zones"]], axis=0)
    st_d = np.min([dist_m(up, la, lo) for la, lo in station_positions(site_name).values()], axis=0)
    tie = (zone_d > C.EXCLUDE_KM * 1000) & (st_d > C.STATION_HOLDOUT_M)
    v = up.mean_velocity.to_numpy()

    def describe(m):
        x = v[m]
        med = float(np.median(x))
        return dict(points=int(m.sum()), median=round(med, 2), p05=round(float(np.percentile(x, 5)), 2),
                    p95=round(float(np.percentile(x, 95)), 2),
                    robust_scatter=round(float(1.4826 * np.median(np.abs(x - med))), 2),
                    share_abs_below_1_5=round(float(np.mean(np.abs(x) < 1.5)), 3),
                    share_below_minus_5=round(float(np.mean(x <= -5)), 4))

    # where the "stable" tie area is not stable: 1 km squares with at least 3 cells sinking 5 mm/yr or faster
    moving = up[tie & (v <= -5)]
    sq = moving.assign(kx=(moving.dx_km // 1).astype(int), ky=(moving.dy_km // 1).astype(int))
    g = sq.groupby(["kx", "ky"]).agg(cells=("mean_velocity", "size"), median=("mean_velocity", "median"),
                                     lat=("lat", "mean"), lon=("lon", "mean"))
    g = g[g.cells >= 3].sort_values("cells", ascending=False).head(10)
    patches = [dict(lat=round(r.lat, 4), lon=round(r.lon, 4), cells=int(r.cells), median=round(float(r.median), 1),
                    km_from_centre=round(C.haversine_km(site["lat"], site["lon"], r.lat, r.lon), 1))
               for r in g.itertuples()]
    check6 = (np.abs(v) < 1.5) & (zone_d > 500)
    return dict(tie_area=describe(tie), check6_set=describe(check6), moving_patches_in_tie_area=patches,
                stations=sorted(station_positions(site_name))), tie


def series(df, mask):
    import pandas as pd
    cols = [c for c in df.columns if c.isdigit() and len(c) == 8]
    s = df.loc[mask, cols].median()
    s.index = pd.to_datetime(cols)
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site", choices=["ocnele_mari"])
    ap.add_argument("--zips", default=str(C.DATA / "egms"), help="folder with the two EGMS Ortho zips")
    ap.add_argument("--release", default="2020_2025_1", help="EGMS release in the file names")
    a = ap.parse_args()

    import pathlib

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    site = C.SITES[a.site]
    zips = pathlib.Path(a.zips)
    up, ew = cut(load(zips, "U", a.release), site), cut(load(zips, "E", a.release), site)
    dates = [c for c in up.columns if c.isdigit() and len(c) == 8]
    refs = C.site_dir(a.site, "refs")
    for df, name in ((up, "egms_up.csv"), (ew, "egms_east.csv")):
        df[["lon", "lat", "mean_velocity"]].rename(columns={"mean_velocity": "v"}).round(
            {"lon": 6, "lat": 6, "v": 2}).to_csv(refs / name, index=False)

    zones = {}
    for comp, df in (("up", up), ("east", ew)):
        for zid, m in zone_masks(df, site).items():
            v, last = df.loc[m, "mean_velocity"], series(df, m)
            zones.setdefault(zid, {})[comp] = dict(
                cells=int(m.sum()),
                v_median=round(float(v.median()), 2) if m.any() else None,
                v_min=round(float(v.min()), 2) if m.any() else None,
                cumulative_mm=round(float(last.iloc[-1]), 1) if m.any() else None)
    meta = dict(source=f"Copernicus EGMS L3 Ortho, tile {TILE}, release {a.release}", crs_in=f"EPSG:{EGMS_EPSG}",
                period=[f"{dates[0][:4]}-{dates[0][4:6]}-{dates[0][6:]}",
                        f"{dates[-1][:4]}-{dates[-1][4:6]}-{dates[-1][6:]}"],
                epochs=len(dates), window_half_km=site["half_km"], points=int(len(up)),
                units="mm/yr; up positive (sinking negative), east positive", zones=zones)
    meta["stable_ground"], tie = stable_ground(up, site, a.site)
    C.save_json(refs / "egms_meta.json", meta)

    figs = C.DOCS / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    inner = up[(up.dx_km.abs() <= 5) & (up.dy_km.abs() <= 5)]
    fig, ax = plt.subplots(figsize=(7, 6), constrained_layout=True)
    sc = ax.scatter(inner.lon, inner.lat, c=inner.mean_velocity, cmap="RdBu", vmin=-10, vmax=10, s=6, marker="s")
    from matplotlib.patches import Ellipse
    import numpy as np
    for z in site["zones"]:
        h = 2 * z["r_m"] / 111_320
        ax.add_patch(Ellipse((z["lon"], z["lat"]), h / np.cos(np.radians(z["lat"])), h, fill=False, lw=1.2))
        ax.annotate(z["id"], (z["lon"], z["lat"]), xytext=(6, 6), textcoords="offset points", fontsize=9)
    ax.set_title(f"EGMS Ortho Up, {meta['period'][0]} to {meta['period'][1]}")
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    fig.colorbar(sc, label="mm/yr (red = sinking)")
    fig.savefig(figs / "05_egms_up_rate.png", dpi=110)

    fig, ax = plt.subplots(figsize=(9, 4.5), constrained_layout=True)
    for zid, m in zone_masks(up, site).items():
        if m.any():
            ax.plot(series(up, m), label=f"{zid} ({int(m.sum())} cells)", lw=2 if zid == "stable" else 1.2)
    ax.axhline(0, color="grey", lw=0.6)
    ax.set_ylabel("cumulative Up, mm")
    ax.set_title("EGMS Ortho Up: median per zone and on stable ground")
    ax.legend(fontsize=8)
    fig.savefig(figs / "05_egms_zone_history.png", dpi=110)

    # the tie area as EGMS sees it: grey = within ±1.5 mm/yr, coloured = moving
    sg = meta["stable_ground"]
    t = up[tie]
    still = t[t.mean_velocity.abs() < 1.5]
    moves = t[t.mean_velocity.abs() >= 1.5]
    fig, ax = plt.subplots(figsize=(8, 7.5), constrained_layout=True)
    ax.scatter(still.dx_km, still.dy_km, s=1, c="#c8c8c8", label=f"|v| < 1.5 mm/yr ({len(still)})")
    sc = ax.scatter(moves.dx_km, moves.dy_km, s=3, c=moves.mean_velocity, cmap="RdBu", vmin=-10, vmax=10,
                    label=f"|v| ≥ 1.5 mm/yr ({len(moves)})")
    for p in sg["moving_patches_in_tie_area"][:5]:
        x = (p["lon"] - site["lon"]) * 111.32 * np.cos(np.radians(site["lat"]))
        y = (p["lat"] - site["lat"]) * 111.32
        ax.add_patch(plt.Rectangle((x - 0.6, y - 0.6), 1.2, 1.2, fill=False, lw=1.2))
        ax.annotate(f"{p['median']}", (x, y), xytext=(8, 8), textcoords="offset points", fontsize=8)
    ax.set_aspect("equal")
    ax.set_xlabel("km east of the window centre")
    ax.set_ylabel("km north")
    ax.set_title(f"EGMS Up on the tie area (zones + {C.EXCLUDE_KM:g} km and stations excluded): "
                 f"median {sg['tie_area']['median']} mm/yr", fontsize=10)
    ax.legend(loc="lower left", fontsize=8, markerscale=4)
    fig.colorbar(sc, label="mm/yr (red = sinking)")
    fig.savefig(figs / "05_egms_stable_ground.png", dpi=100)

    print(f"egms: {len(up)} points in the {2 * site['half_km']} km window, {meta['period'][0]} to {meta['period'][1]}, "
          f"{len(dates)} epochs → {refs / 'egms_up.csv'}")
    for zid, z in zones.items():
        print(f"  {zid:6s} up {z['up']['v_median']} mm/yr (min {z['up']['v_min']}, {z['up']['cells']} cells, "
              f"{z['up']['cumulative_mm']} mm total)   east {z['east']['v_median']} mm/yr")
    for k in ("tie_area", "check6_set"):
        s = sg[k]
        print(f"  {k:10s} {s['points']} points: median {s['median']} mm/yr, robust scatter {s['robust_scatter']}, "
              f"5-95 % {s['p05']} to {s['p95']}, |v|<1.5: {100 * s['share_abs_below_1_5']:.0f} %, "
              f"≤ −5: {100 * s['share_below_minus_5']:.1f} %")
    for p in sg["moving_patches_in_tie_area"]:
        print(f"    moving patch in tie area: {p['lat']} N {p['lon']} E, {p['km_from_centre']} km out, "
              f"{p['cells']} cells, median {p['median']} mm/yr")


if __name__ == "__main__":
    C.run_cli(main)
