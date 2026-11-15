# Owner: 06 · App developer (Darius)
"""06 · App developer: turn the science outputs into what the page reads: products/<site>/.

Status: WORKS for Sentinel-1 (Jul to Oct 2026 fit) and NISAR (fetch.py → stack.py → calibrate.py, 14 Nov 2026). NISAR is
exported when data/work/<site>/<track>/ts.npz exists for a track (cal.npz preferred: GNSS-tied); otherwise the page keeps
"Displacement fit pending" for it.

    python export.py ocnele_mari

Reads (never writes) these inputs:
  Sentinel-1 (03): sentinel1/analysis/summary.json and the grid chunks in sentinel1/assets/ (029A, 007D). The chunks
      are joined in memory and checked against sentinel1/assets/SHA256SUMS; nothing is written into sentinel1/.
  NISAR (02): data/scenes/ocnele_mari_gunw.csv, the 22 public GUNW pairs (catalog coverage); per track, if present,
      data/work/<site>/<track>/meta.json, ts.npz (03) and cal.npz (04).
  common.py: site, view (D-002), zones, sensors, common window.
Writes products/<site>/ (file contracts in docs/build-spec.md, design in docs/ui.md):
  manifest.json      sensors.{nisar,s1}, views, default (NISAR Coverage), windows, methods, credits
  s1/frames/<track>/<date>.png   cumulative line-of-sight change since the first date, lon/lat grid, RdBu
  s1/los_<track>.png             line-of-sight rate (annualized short-window slope)
  s1/points_<track>.json         the same values as map dots, one every 80 m (the page draws these; the PNGs stay
                                 as a fallback and for the GeoTIFF-free slides)
  nisar/frames/<track>/<date>.png, nisar/los_<track>.png, nisar/points_<track>.json   the same for NISAR (80 m grid;
                                 frames are cumulative since the first date of the date's acquisition group; dots only
                                 inside the Sentinel-1 box, 16.4 km around the town, to keep the file small)
  series.json        zone and outer-comparison histories, keyed "s1:<track>" and "nisar:<track>"
  sensitivity.json   per window: frames, layers, and every processing scenario per track and zone
  coverage.json      acquisition dates per sensor and track; NISAR pairs from the catalog; usable zone pixels
  stations.geojson, calib.json, checks.json   only if missing, as explicit "pending" files: 04 and 05 own them
and adds the site to products/index.json.

Choices (logged in DECISIONS.md): colours fixed at ±20 mm for change and ±40 mm/yr for rate on every track, so both
satellites share one legend; values beyond the scale are drawn at full colour and the legend says so. Missing pixels
stay transparent. No experimental up/east layer is exported (03 and 04 have not signed it off; how to compare the two radars is still undecided).
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import io
import json
import pathlib

import common as C

S1_DIR = C.ROOT / "sentinel1"
SCENES = C.DATA / "scenes" / "ocnele_mari_gunw.csv"
CHANGE_VMAX = 20.0      # mm, frames (same scale as mock_products.py, shared by both satellites)
RATE_VMAX = 40.0        # mm/yr, rate layers
PX_DEG = 0.0005         # output pixel size in degrees of latitude (about 55 m; the grids are 40 m)
POINT_STEP = 2          # points: one per 2 × 2 block of 40 m pixels, i.e. one dot every 80 m (its top-left pixel)
SCENARIOS = {           # summary.json fit name → label on the page
    "baseline": "Baseline (coherence ≥ 0.35)",
    "strict_coherence": "Stricter coherence (≥ 0.55)",
    "west_reference": "West reference area only",
    "east_reference": "East reference area only",
    "elevation_correction": "Elevation correction (fitted to the data)",
    "weather_model": "Weather-model troposphere (ECMWF IFS, acquisition time)",
}
WINDOW = "jul_oct"
# Sentinel-1 windows. jul_oct is the default; jan_oct (049 dates, 1 Jan to 5 Oct 2026) covers NISAR's 18 Jan to 23 Jun
# gap, so the page offers it there (docs/ui.md, "Sentinel-1 fills NISAR's gap", 15 Nov 2026).
S1_WINDOWS = {
    "jul_oct": dict(label="July to October 2026", analysis="analysis", assets="assets", prefix="s1"),
    "jan_oct": dict(label="January to October 2026", analysis="analysis_jan_oct", assets="assets_jan_oct", prefix="s1/jan_oct"),
}
# What the page says when a zone has no series in a window (docs/ui.md, "Zone review and historical context"):
# July to October: the zone has no connected pixels on that track; January to October: no zone pixel stays connected
# across all 49 dates, so the extended fit gives no continuous series.
EMPTY_ZONE_LABEL = {
    "jul_oct": "No connected series for this zone on this track",
    "jan_oct": "Insufficient continuous coverage",
}

# Interpretation labels from 03's zone review (sentinel1/docs/TEAM_HANDOFF.md, "Group-aware refit and EGMS
# cross-check", and docs/ui.md, "Zone review and historical context", 14 Nov 2026). Text only: no value is changed.
REVIEW = "03 zone review, 14 Nov 2026 (sentinel1/docs/TEAM_HANDOFF.md)"
ZONE_NOTES = {
    "z3": dict(label="Historically subsiding · 2026 trend inconclusive",
               detail="EGMS history shows this zone sinking, but the 2026 Sentinel-1 evidence is limited: no connected "
                      "ascending (029A) series in July to October, and the descending (007D) result changes sign across "
                      "processing runs. Over January to October no zone pixel stays connected on either track.",
               source=REVIEW),
}
TRACK_NOTES = {
    "s1:029A": dict(zones=["z1", "z2", "z4"], label="Local reference sensitivity",
                    detail="On 029A, terrain near the zones also shows a negative line-of-sight signal, so part of a zone "
                           "value may come from the reference area, the atmosphere or the geometry rather than the zone. "
                           "The values are shown as measured, without a correction.",
                    source=REVIEW),
}


# ------------------------------------------------------------------------------------------------ inputs
def iso(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def load_summary(window: str = WINDOW) -> dict:
    return json.loads((S1_DIR / S1_WINDOWS[window]["analysis"] / "summary.json").read_text(encoding="utf-8"))


def load_grid(track: str, window: str = WINDOW):
    """Join the committed chunks of <track>.npz in memory and check them against SHA256SUMS."""
    import numpy as np
    w = S1_WINDOWS[window]
    sums = {name: digest for digest, name in (l.split() for l in (S1_DIR / w["assets"] / "SHA256SUMS").read_text().splitlines())}
    payload = b"".join(p.read_bytes() for p in sorted((S1_DIR / w["assets"]).glob(f"{track}.npz.part*")))
    if hashlib.sha256(payload).hexdigest() != sums[f"{w['analysis']}/{track}.npz"]:
        raise SystemExit(f"sentinel1/{w['assets']}/{track}.npz.part*: checksum mismatch, the grids do not match SHA256SUMS")
    return np.load(io.BytesIO(payload), allow_pickle=False)


# ------------------------------------------------------------------------------------------------ rasters
class LonLatGrid:
    """A regular lon/lat display grid covering a UTM box, with a nearest-neighbour lookup into the UTM grid."""

    def __init__(self, bounds_utm, shape, epsg: int = 32635):
        import numpy as np
        from pyproj import Transformer
        xmin, ymin, xmax, ymax = bounds_utm
        ny, nx = shape
        self.dx, self.dy = (xmax - xmin) / nx, (ymax - ymin) / ny
        to_ll = Transformer.from_crs(epsg, 4326, always_xy=True)
        lon, lat = to_ll.transform([xmin, xmax, xmin, xmax], [ymin, ymin, ymax, ymax])
        # inner box so every display pixel lies inside the UTM grid
        self.W, self.E = max(lon[0], lon[2]), min(lon[1], lon[3])
        self.S, self.N = max(lat[0], lat[1]), min(lat[2], lat[3])
        h = int(round((self.N - self.S) / PX_DEG))
        w = int(round((self.E - self.W) * np.cos(np.radians((self.N + self.S) / 2)) / PX_DEG))   # square pixels on the ground
        lats = self.N - (np.arange(h) + 0.5) * (self.N - self.S) / h
        lons = self.W + (np.arange(w) + 0.5) * (self.E - self.W) / w
        LON, LAT = np.meshgrid(lons, lats)
        x, y = Transformer.from_crs(4326, epsg, always_xy=True).transform(LON, LAT)
        self.col = np.clip(((x - xmin) / self.dx).astype(int), 0, nx - 1)
        self.row = np.clip(((ymax - y) / self.dy).astype(int), 0, ny - 1)   # row 0 is north
        self.shape = (h, w)

    def sample(self, arr):
        return arr[self.row, self.col]

    @property
    def bounds(self):
        return [[round(self.S, 6), round(self.W, 6)], [round(self.N, 6), round(self.E, 6)]]


def write_points(z, path: pathlib.Path, track: str, dates: list[str], epsg: int = 32635) -> int:
    """Measurement points for the map's dot layer: one every POINT_STEP pixels, values in 0.1 mm (null = no data).

    The values are the grid's own pixels (sampled, not averaged), so a dot shows exactly what the fit gives there.
    """
    import numpy as np
    from pyproj import Transformer
    xmin, ymin, xmax, ymax = z["bounds_utm"]
    rate = z["rate_mm_yr"]; disp = z["displacement_mm"]
    ny, nx = rate.shape
    dx, dy = (xmax - xmin) / nx, (ymax - ymin) / ny
    rows, cols = np.mgrid[0:ny:POINT_STEP, 0:nx:POINT_STEP]
    rows, cols = rows.ravel(), cols.ravel()
    keep = np.isfinite(rate[rows, cols]) | np.isfinite(disp[:, rows, cols]).any(axis=0)
    rows, cols = rows[keep], cols[keep]
    x = xmin + (cols + 0.5) * dx
    y = ymax - (rows + 0.5) * dy                       # row 0 is north
    lon, lat = Transformer.from_crs(epsg, 4326, always_xy=True).transform(x, y)
    tenth = lambda a: [None if not np.isfinite(v) else int(round(float(v) * 10)) for v in a]
    obj = dict(track=track, dates=[iso(d) for d in dates], spacing_m=round(dx * POINT_STEP), scale=0.1,
               units=dict(change="mm since first date", rate="mm/yr"),
               lon=[round(float(v), 5) for v in lon], lat=[round(float(v), 5) for v in lat],
               rate=tenth(rate[rows, cols]), change=[tenth(disp[k, rows, cols]) for k in range(len(dates))])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, separators=(",", ":")), encoding="utf-8")
    return len(rows)


def overlay_png(arr, path: pathlib.Path, vmax: float) -> None:
    """RdBu PNG: red = negative (away from the satellite), blue = positive; NaN transparent; beyond ±vmax saturated."""
    import numpy as np
    from PIL import Image
    stops = np.array([[103, 0, 31], [214, 96, 77], [247, 247, 247], [67, 147, 195], [5, 48, 97]], float)
    v = np.clip(np.nan_to_num(arr, nan=0.0) / vmax, -1, 1)
    pos = (v + 1) / 2 * (len(stops) - 1)
    i = np.clip(pos.astype(int), 0, len(stops) - 2)
    f = (pos - i)[..., None]
    rgb = stops[i] * (1 - f) + stops[i + 1] * f
    alpha = np.where(np.isfinite(arr), 230, 0)
    img = np.dstack([rgb, alpha]).round().astype("uint8")
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img, "RGBA").save(path, optimize=True)


# ------------------------------------------------------------------------------------------------ Sentinel-1
def town_cover(rate, bounds_utm, epsg: int = 32635) -> int:
    """Share (%) of the grid cells inside the town boundary (app/ocnele_mari_boundary.geojson) that have a rate."""
    import numpy as np
    from matplotlib.path import Path
    from pyproj import Transformer
    f = C.ROOT / "app" / "ocnele_mari_boundary.geojson"
    if not f.exists():
        return -1
    g = C.load_json(f)
    geom = g["features"][0]["geometry"] if "features" in g else g
    ring = np.array(geom["coordinates"][0] if geom["type"] == "Polygon" else geom["coordinates"][0][0])
    ny, nx = rate.shape
    x0, y0, x1, y1 = bounds_utm
    J, I = np.meshgrid(np.arange(nx), np.arange(ny))
    lon, lat = Transformer.from_crs(epsg, 4326, always_xy=True).transform(x0 + (J + .5) * (x1 - x0) / nx,
                                                                         y1 - (I + .5) * (y1 - y0) / ny)
    inside = Path(ring).contains_points(np.c_[lon.ravel(), lat.ravel()]).reshape(rate.shape)
    return int(round(100 * float(np.isfinite(rate)[inside].mean()))) if inside.any() else -1


def export_s1(out: pathlib.Path, summary: dict, window: str = WINDOW):
    """→ (sensor block for the manifest, display bounds)."""
    meta = C.SENSORS["s1"]
    pre = S1_WINDOWS[window]["prefix"]
    frames, layers, bounds, points, cover = {}, [], None, {}, {}
    for track in meta["tracks"]:
        z = load_grid(track, window)
        cover[track] = town_cover(z["rate_mm_yr"], z["bounds_utm"])
        dates = [str(d) for d in z["dates"]]
        if dates != summary[track]["dates"]:
            raise SystemExit(f"{track}: grid dates differ from sentinel1/analysis/summary.json; ask 03 to repack the grids")
        grid = LonLatGrid(z["bounds_utm"], z["rate_mm_yr"].shape)
        bounds = bounds or grid.bounds
        pngs = []
        for k, d in enumerate(dates):
            png = f"{pre}/frames/{track}/{iso(d)}.png"
            overlay_png(grid.sample(z["displacement_mm"][k]), out / png, CHANGE_VMAX)
            pngs.append(png)
        frames[track] = dict(dates=[iso(d) for d in dates], pngs=pngs, vmin=-CHANGE_VMAX, vmax=CHANGE_VMAX,
                             units="mm since first date", direction=meta["tracks"][track], gaps=[],
                             window=window, saturates=True)
        png = f"{pre}/los_{track}.png"
        overlay_png(grid.sample(z["rate_mm_yr"]), out / png, RATE_VMAX)
        pts_file = f"{pre}/points_{track}.json"
        n_pts = write_points(z, out / pts_file, track, dates)
        points[track] = pts_file
        layers.append(dict(id=f"los_{track}", label=f"Sentinel-1 {track}: line-of-sight rate, annualized short-window slope",
                           png=png, units="mm/yr", vmin=-RATE_VMAX, vmax=RATE_VMAX, track=track, experimental=False,
                           window=window, scenario="baseline", saturates=True))
        print(f"  s1 {window} {track}: {len(dates)} frames + rate map + {n_pts} points, {grid.shape[1]}×{grid.shape[0]} px, "
              f"{dates[0]}..{dates[-1]}, {summary[track]['pair_count']} pairs, town covered {cover[track]} %")
    block = {k: meta[k] for k in ("label", "agency", "band", "wavelength_cm", "status", "reference", "credit")}
    block.update(layers=layers, frames=frames, points=points, look=meta["look"], product=meta["product"], town_cover=cover)
    return block, bounds


def zone_points(site: dict) -> list[dict]:
    pts = []
    for z in site["zones"]:
        n = z["id"].lstrip("z")
        pts.append(dict(id=z["id"], key=f"zone_{n}", label=C.zone_label(z), kind="zone", lat=z["lat"], lon=z["lon"],
                        r_m=z["r_m"], place=z.get("place")))
    pts.append(dict(id="outer_control", key="outer_control", label="Outer comparison area (6.5 to 8 km)", kind="control",
                    lat=site["lat"], lon=site["lon"]))
    return pts


def scenario_entry(fit: dict, dates: list[str]) -> dict:
    mm = [None if v is None or v != v else round(v, 2) for v in fit["displacement_mm"]]
    rng = fit.get("date_fit_omission_range_mm_yr") or [None, None]
    return dict(dates=[iso(d) for d in dates], mm=mm, n_pixels=fit["pixels"],
                fitted_change_mm=round(fit["window_fit_mm"], 2), rate=round(fit["linear_mm_yr"], 2),
                theil_sen_mm_yr=round(fit["theil_sen_mm_yr"], 2),
                omission_range_mm_yr=[round(v, 2) for v in rng] if None not in rng else None)


def export_series(summary: dict, site: dict) -> tuple[list[dict], dict]:
    """series.json (baseline) and the per-scenario variants for sensitivity.json."""
    pts = zone_points(site)
    variants = {}
    for track in C.SENSORS["s1"]["tracks"]:
        fits = summary[track]["fits"]
        variants[track] = {}
        for sc in SCENARIOS:
            variants[track][sc] = {}
            for p in pts:
                fit = fits.get(sc, {}).get(p["key"])
                # fit.py records an empty zone explicitly ({"pixels": 0, "status": ...}); that is no series here
                variants[track][sc][p["id"]] = (scenario_entry(fit, summary[track]["dates"])
                                                if fit and "displacement_mm" in fit else None)
    for p in pts:
        p["series"] = {}
        for track in C.SENSORS["s1"]["tracks"]:
            e = variants[track]["baseline"][p["id"]]
            if e:
                p["series"][f"s1:{track}"] = {k: e[k] for k in ("dates", "mm", "rate", "n_pixels", "fitted_change_mm")}
        p.pop("key")
    return pts, variants


# ------------------------------------------------------------------------------------------------ NISAR coverage
def nisar_coverage() -> dict:
    rows = list(csv.DictReader(SCENES.open(encoding="utf-8")))
    cov = {}
    for t in C.SENSORS["nisar"]["tracks"]:
        pairs = sorted((r for r in rows if r["track"] == t), key=lambda r: r["ref_date"])
        dates = sorted({r["ref_date"] for r in pairs} | {r["sec_date"] for r in pairs})
        # a gap is any stretch between consecutive dates that no pair spans
        spans = [(r["ref_date"], r["sec_date"]) for r in pairs]
        gaps = [[a, b] for a, b in zip(dates, dates[1:]) if not any(r <= a and s >= b for r, s in spans)]
        cov[t] = dict(dates=dates, gaps=gaps, direction=C.SENSORS["nisar"]["tracks"][t],
                      pairs=[dict(ref=r["ref_date"], sec=r["sec_date"], days=int(r["days"]), collection=r["collection"])
                             for r in pairs])
    return cov


# ------------------------------------------------------------------------------------------------ NISAR displacement
NISAR_POINT_BOX_M = 8200
# Tracks held off the page until a check clears them (DECISIONS.md, 14 Nov 2026, 23:00). The reason is shown on the page.
NISAR_HOLD = {}            # tracks kept off the page entirely (none since 15 Nov 2026)
# Tracks shown but flagged: they failed a predeclared check and stay visible for inspection, never for interpretation
# (Alexandru, 15 Nov 2026: keep every source, filter at the end). The reason is shown on the page.
NISAR_FLAG = {
    "094D": "Failed the phase-sign test T3: the zones read +23.5 mm/yr against far stable ground, where they should "
            "sink. Unwrapping is ruled out, and neither the ECMWF weather model nor NASA's own troposphere screens "
            "(in the product) remove it; the signal covers the whole valley. Our own pairs from NISAR's raw single-look data reduce it to +3.5 mm/yr (still failing). Shown for inspection, not interpretation "
            "(notebooks/03/t3_094d_checks.json). Summer to autumn only: with June to October dates alone, a seasonal "
            "cycle can bias its rate by about half (test T6, notebooks/03/t5_t6_synthetic.json).",
}    # dots only within this half-size of the site centre (the Sentinel-1 window)


def load_nisar(site_key: str, track: str):
    """→ (meta, ts, values) or None. values: dates, cum (mm, per group from 0), vel (mm/yr), tied (bool)."""
    import numpy as np
    d = C.WORK / site_key / track
    if not (d / "ts.npz").exists():
        return None
    meta = C.load_json(d / "meta.json")
    ts = dict(np.load(d / "ts.npz", allow_pickle=False))
    tied = (d / "cal.npz").exists()
    if tied:
        cal = dict(np.load(d / "cal.npz", allow_pickle=False))
        cum, vel = cal["cum_cal"], cal["vel_cal"]
    else:
        cum, vel = ts["cum"], ts["vel"]
    return meta, ts, dict(dates=[str(x) for x in ts["dates"]], cum=cum, vel=vel, tied=tied)


def nisar_bounds(meta: dict):
    xmin = meta["x0"] - meta["dx"] / 2
    ymax = meta["y0"] - meta["dy"] / 2                   # dy < 0: row 0 is north
    return (xmin, ymax + meta["ny"] * meta["dy"], xmin + meta["nx"] * meta["dx"], ymax)


def nisar_zone_masks(site: dict, meta: dict):
    """Zone discs and the outer comparison ring (6.5 to 8 km from the zone edges), as fit.py draws them for Sentinel-1."""
    import numpy as np
    X = meta["x0"] + np.arange(meta["nx"]) * meta["dx"]
    Y = meta["y0"] + np.arange(meta["ny"]) * meta["dy"]
    X, Y = np.meshgrid(X, Y)
    dist = []
    for z in site["zones"]:
        zx, zy = C.to_xy(meta["epsg"], z["lon"], z["lat"])
        dist.append(np.hypot(X - zx, Y - zy) - z["r_m"])
    off = np.min(dist, axis=0)
    masks = {z["id"]: d <= 0 for z, d in zip(site["zones"], dist)}
    masks["outer_control"] = (off >= 6500) & (off <= 8000)
    return masks


def nisar_series(dates, cum, groups, mask) -> dict | None:
    """Median over the pixels with a value on every date; rate through the dates with one offset per group."""
    import numpy as np
    good = mask & np.isfinite(cum).all(axis=0)
    n = int(good.sum())
    if not n:
        return None
    mm = np.median(cum[:, good], axis=1)
    t = C.years(dates)
    A = np.c_[t, np.eye(len(set(groups)))[groups]]
    rate = float(np.linalg.lstsq(A, mm, rcond=None)[0][0])
    return dict(dates=dates, mm=[round(float(v), 2) for v in mm], rate=round(rate, 2), n_pixels=n,
                fitted_change_mm=round(rate * (t[-1] - t[0]), 2))


def export_nisar(out: pathlib.Path, site_key: str, series: list[dict]):
    """→ (layers, frames, points, notes) for the manifest; adds "nisar:<track>" histories to series in place."""
    import numpy as np
    site = C.SITES[site_key]
    meta_s = C.SENSORS["nisar"]
    layers, frames, points, notes = [], {}, {}, {}
    for track in meta_s["tracks"]:
        got = None if track in NISAR_HOLD else load_nisar(site_key, track)
        if not got:
            continue
        meta, ts, v = got
        dates, cum, vel = v["dates"], v["cum"], v["vel"]
        groups = [int(g) for g in ts["group"]]
        bounds = nisar_bounds(meta)
        grid = LonLatGrid(bounds, vel.shape, meta["epsg"])
        pngs = []
        for k, d in enumerate(dates):
            png = f"nisar/frames/{track}/{d}.png"
            overlay_png(grid.sample(cum[k]), out / png, CHANGE_VMAX)
            pngs.append(png)
        gaps = [list(g) for g in ts["gap_ranges"]]
        frames[track] = dict(dates=dates, pngs=pngs, vmin=-CHANGE_VMAX, vmax=CHANGE_VMAX,
                             units="mm since the first date of its acquisition group", direction=meta_s["tracks"][track],
                             gaps=gaps, window="nisar", saturates=True, groups=groups, flag=NISAR_FLAG.get(track))
        png = f"nisar/los_{track}.png"
        overlay_png(grid.sample(vel), out / png, RATE_VMAX)
        layers.append(dict(id=f"los_{track}", label=f"NISAR {track}: line-of-sight rate through the dates"
                           + (", tied to EuVeM2022" if v["tied"] else ", terrain-relative"),
                           png=png, units="mm/yr", vmin=-RATE_VMAX, vmax=RATE_VMAX, track=track, experimental=False,
                           window="nisar", scenario="baseline", saturates=True))
        # dots: crop to the Sentinel-1 box so the file stays small
        cx, cy = C.to_xy(meta["epsg"], site["lon"], site["lat"])
        X = meta["x0"] + np.arange(meta["nx"]) * meta["dx"]
        Y = meta["y0"] + np.arange(meta["ny"]) * meta["dy"]
        cs = np.where(np.abs(X - cx) <= NISAR_POINT_BOX_M)[0]
        rs = np.where(np.abs(Y - cy) <= NISAR_POINT_BOX_M)[0]
        sub = np.s_[rs[0]:rs[-1] + 1, cs[0]:cs[-1] + 1]
        zb = (X[cs[0]] - meta["dx"] / 2, Y[rs[-1]] + meta["dy"] / 2, X[cs[-1]] + meta["dx"] / 2, Y[rs[0]] - meta["dy"] / 2)
        pts_file = f"nisar/points_{track}.json"
        global POINT_STEP
        step, POINT_STEP = POINT_STEP, 1                     # NISAR pixels are already 80 m
        try:
            n_pts = write_points(dict(bounds_utm=zb, rate_mm_yr=vel[sub], displacement_mm=cum[(slice(None),) + sub]),
                                 out / pts_file, track, [d.replace("-", "") for d in dates], meta["epsg"])
        finally:
            POINT_STEP = step
        points[track] = pts_file
        masks = nisar_zone_masks(site, meta)
        for p in series:
            e = nisar_series(dates, cum, groups, masks[p["id"]])
            if e:
                p["series"][f"nisar:{track}"] = e
        notes[track] = dict(tied=v["tied"], pairs=int(ts["n_pairs"]), groups=len(set(groups)),
                            phase_sign=int(ts["phase_sign"]), iono_used=int(np.sum(ts["iono_used"])))
        print(f"  nisar {track}: {len(dates)} frames + rate map + {n_pts} points, {grid.shape[1]}×{grid.shape[0]} px, "
              f"{dates[0]}..{dates[-1]}, {int(ts['n_pairs'])} pairs, {'GNSS-tied' if v['tied'] else 'terrain-relative'}")
    return layers, frames, points, notes


# ------------------------------------------------------------------------------------------------ the products set
def write_pending(out: pathlib.Path) -> list[str]:
    """stations.geojson, calib.json, checks.json belong to 04 and 05; write explicit pending files only if missing."""
    made = []
    pending = {
        "stations.geojson": dict(type="FeatureCollection", features=[], pending="validate.py (05) has not compared stations yet"),
        "calib.json": dict(model=None, tracks=[], pending="calibrate.py (04) has not tied NISAR to the GNSS model yet"),
        "checks.json": [dict(id="validation-pending", status="info", title="Validation not run yet",
                             detail="validate.py (05) has not written checks for this build", value=None)],
    }
    for name, obj in pending.items():
        if not (out / name).exists():
            C.save_json(out / name, obj)
            made.append(name)
    return made


def egms_block(out: pathlib.Path) -> dict:
    """The EGMS history block. A reported summary already in manifest.json (added by 03 from 05's pinned validation
    log, 14 Nov 2026) is carried forward unchanged; otherwise the block says "pending". 05 should own this as a file."""
    try:
        old = C.load_json(out / "manifest.json").get("egms") or {}
    except (FileNotFoundError, ValueError):
        old = {}
    if old.get("status") not in (None, "pending") and old.get("summary") and old.get("source"):
        return old
    return dict(status="pending", label="EGMS Ortho · 2020 to 2025 · 100 m",
                detail="The E54N25 extracts (05) are not verified yet. EGMS history gives context; it cannot verify a 2026 rate.")


def run(site_key: str) -> None:
    if C.SITES[site_key].get("synthetic"):
        raise C.todo("06", "export the synthetic demo site once fetch/stack/calibrate --synthetic exist")
    site = C.SITES[site_key]
    out = C.PRODUCTS / site_key
    out.mkdir(parents=True, exist_ok=True)
    summary = load_summary()

    s1, bounds = export_s1(out, summary)
    series, variants = export_series(summary, site)
    n_layers, n_frames_, n_points, n_notes = export_nisar(out, site_key, series)
    C.save_json(out / "series.json", series)
    cov = nisar_coverage()
    C.save_json(out / "coverage.json", dict(
        nisar={t: c for t, c in cov.items()},
        s1={t: dict(dates=s1["frames"][t]["dates"], gaps=[], direction=C.SENSORS["s1"]["tracks"][t],
                    pairs=summary[t]["pair_count"],
                    zone_pixels={p["id"]: (variants[t]["baseline"][p["id"]] or {}).get("n_pixels") for p in series})
            for t in s1["frames"]},
        source=dict(nisar="data/scenes/ocnele_mari_gunw.csv (NASA CMR, 14 Nov 2026)",
                    s1="sentinel1/analysis/summary.json (03)")))
    windows = {WINDOW: dict(label="July to October 2026", empty_zone_label=EMPTY_ZONE_LABEL[WINDOW], dates={t: [f["dates"][0], f["dates"][-1]] for t, f in s1["frames"].items()},
                            frames=s1["frames"], layers=s1["layers"], points=s1["points"], variants=variants,
                            maps_scenario="baseline", town_cover=s1["town_cover"],
                            quality={t: summary[t]["fits"]["quality"] for t in s1["frames"]})}
    sj = load_summary("jan_oct")
    s1j, _ = export_s1(out, sj, "jan_oct")
    _, variants_j = export_series(sj, site)
    windows["jan_oct"] = dict(label=S1_WINDOWS["jan_oct"]["label"], empty_zone_label=EMPTY_ZONE_LABEL["jan_oct"],
                              dates={t: [f["dates"][0], f["dates"][-1]] for t, f in s1j["frames"].items()},
                              frames=s1j["frames"], layers=s1j["layers"], points=s1j["points"], variants=variants_j,
                              maps_scenario="baseline", town_cover=s1j["town_cover"],
                              quality={t: sj[t]["fits"].get("quality") for t in s1j["frames"]},
                              fills_gap=dict(sensor="nisar", gap=["2026-01-18", "2026-06-23"],
                                             note="Sentinel-1 kept imaging the town while NISAR had no acquisitions. Its "
                                                  "values are its own line of sight and reference, not NISAR's."),
                              provenance="sentinel1/analysis_jan_oct/README.md (job IDs only; not reproducible from the repository alone)")
    C.save_json(out / "sensitivity.json", dict(windows=windows, scenarios=SCENARIOS, default_window=WINDOW,
                                                note="Selectors choose stored results; maps exist for the baseline only. "
                                                     "The single-date omission range is diagnostic, not a confidence interval."))
    made = write_pending(out)
    checks = C.load_json(out / "checks.json")

    nmeta = C.SENSORS["nisar"]
    nisar = {k: nmeta[k] for k in ("label", "agency", "band", "wavelength_cm", "status", "reference", "credit")}
    nisar.update(layers=n_layers, frames=n_frames_, points=n_points, look=nmeta["look"], product=nmeta["product"],
                 fit=n_notes, flags={t: r for t, r in NISAR_FLAG.items() if t in n_frames_})
    missing = [t for t in nmeta["tracks"] if t not in n_frames_]
    if missing:
        nisar["pending"] = (" ".join(NISAR_HOLD.get(t, f"{t}: displacement fit pending.") for t in missing) if n_frames_ else
                            "Displacement fit pending: authenticated download, independent fit and line-of-sight sign "
                            "check are not done yet. Catalog coverage only.")
    C.save_json(out / "manifest.json", dict(
        site=site_key, name=f"{site['name']}, {site['county']}", story=site["story"], synthetic=False,
        note=("Sentinel-1 measurements (Jul to Oct 2026) and NISAR measurements (" + ", ".join(sorted(n_frames_)) + ")."
              if n_frames_ else "Sentinel-1 measurements (Jul to Oct 2026) and NISAR catalog coverage. NISAR displacement is pending."),
        built=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        bounds=bounds, center=[site["lat"], site["lon"]], view=dict(site["view"], min_zoom=6, context="romania-blurred"),
        sensors=dict(nisar=nisar, s1=s1), views=list(C.VIEWS), common_window=list(C.COMMON_WINDOW),
        default=dict(sat="nisar", view="coverage", track="129A"),
        compare=dict(ready=bool(n_frames_),
                     pairs={"129A": "007D", "094D": "029A"},   # same east sensitivity: NISAR looks left, Sentinel-1 right
                     reason=("Side by side, each satellite in its own line of sight. Tracks are paired by geometry (NISAR "
                             "129A with Sentinel-1 007D: both see east-west motion the same way). The verdict per zone "
                             "comes from the validator; a shared quantity (open team decision: how to compare the two radars) is still open.")),
        windows={k: v["label"] for k, v in windows.items()}, default_window=WINDOW,
        checks={k: sum(c.get("status") == k for c in checks) for k in ("pass", "warn", "fail", "info")},
        zone_notes=ZONE_NOTES, track_notes=TRACK_NOTES,
        egms=egms_block(out),
        methods=dict(
            s1="Sentinel-1 IW2 VV bursts 029_060407_IW2 and 007_013694_IW2, processed by ASF HyP3 (10×2 looks, water mask) "
               "and inverted on a 40 m grid with coherence-squared weights. Each pair is zeroed on a terrain reference band "
               "3 to 6.5 km from the zone edges; the outer comparison area is 6.5 to 8 km. Not GNSS-calibrated.",
            sign="Line of sight, positive toward the satellite. Red is away from the satellite, blue is toward.",
            rate="A rate is a fitted annualized slope over the window, not a long-term velocity. No per-pixel uncertainty layer is validated yet.",
            nisar="NISAR L2 GUNW (frequency A, HH, 80 m) streamed over the 50 km window by fetch.py: mask decoded as a "
                  "bitfield, largest connected component, ionosphere screen subtracted. stack.py: coherence ≥ 0.35, "
                  "elevation slope and stable-ground reference removed per pair, small-baseline inversion with one "
                  "group per side of the January to June gap, rate through the dates. calibrate.py ties each track to "
                  "EuVeM2022 on stable ground. Beta and provisional products, not intended for scientific research.",
            zones="Four zone circles from the advisor's starter kit (permission to publish them is still to be confirmed).",
            links=[dict(label="Sentinel-1 team handoff", href="sentinel1/docs/TEAM_HANDOFF.md"),
                   dict(label="Sentinel-1 analysis notes", href="sentinel1/analysis/README.md"),
                   dict(label="NISAR pair list", href="data/scenes/ocnele_mari_gunw.csv"),
                   dict(label="ASF NISAR Data User Guide", href="https://nisar-docs.asf.alaska.edu/")]),
        credits="Contains modified Copernicus Sentinel data 2026, processed by ASF HyP3. NISAR catalog: NASA–ISRO, ASF DAAC "
                "(beta and provisional products, not intended for scientific research).",
    ))
    idx = C.PRODUCTS / "index.json"
    sites = C.load_json(idx) if idx.exists() else []
    sites = [s for s in sites if s.get("site") != site_key] + [dict(site=site_key, name=site["name"], synthetic=False)]
    C.save_json(idx, sorted(sites, key=lambda s: (s["synthetic"], s["site"])))
    n_frames = sum(len(f["dates"]) for f in s1["frames"].values())
    print(f"{out}: s1 {len(s1['layers'])} rate maps, {n_frames} frames, {len(series)} series points · "
          f"nisar {len(n_layers)} rate maps, {sum(len(f['dates']) for f in n_frames_.values())} frames, "
          f"coverage {sum(len(c['pairs']) for c in cov.values())} pairs"
          + (f" · pending files written: {', '.join(made)}" if made else ""))


def relabel(site_key: str) -> None:
    """Copy the zone names from common.py into an existing series.json without re-exporting any data."""
    site = C.SITES[site_key]
    f = C.PRODUCTS / site_key / "series.json"
    names = {p["id"]: p for p in zone_points(site) if p["kind"] == "zone"}
    series = C.load_json(f)
    for p in series:
        if p.get("id") in names:
            p["label"], p["place"] = names[p["id"]]["label"], names[p["id"]]["place"]
    C.save_json(f, series)
    print(f"{f}: zone labels {', '.join(n['label'] for n in names.values())}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    ap.add_argument("--labels-only", action="store_true", help="only copy the zone names from common.py into series.json")
    a = ap.parse_args()
    relabel(a.site) if a.labels_only else run(a.site)


if __name__ == "__main__":
    C.run_cli(main)
