# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Zero-shot Chronos-2 forecasts to 1 January 2029 for the whole town, not only the four salt zones.

    python forecast_area.py ../../products/ocnele_mari    (environment with chronos-forecasting >= 2, CPU torch)

Every measured point inside Ocnele Mari's administrative boundary (app/ocnele_mari_boundary.geojson, OpenStreetMap) is
grouped into 240 m cells (3 × 3 points of the 80 m grid). A cell with at least 3 points gets the median series of its
points, and Chronos-2 forecasts it with the same settings as forecast_zones.py (zero-shot, 6-day steps, median and 80 %
range). The page combines the cells inside whatever the user selects (a square, a zone, a pin or a house).

Series: Sentinel-1 029A from the May 2025 to November 2026 window (s1/all), 007D from July to November 2026 (s1/jul_nov:
its long window keeps only 8 points in town through the winters), NISAR from June 2026 on (after its January to June
gap, re-zeroed at the first date there). Backtest: each cell's last 60 days are forecast from the data before them and
scored against the measured values and against "no further change"; the page shows the median error over the cells.
Writes <products>/forecast_area.json.
"""
import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

END, STEP, Q, CELL_M, MIN_PTS = date(2029, 1, 1), 6.0, [0.1, 0.5, 0.9], 240, 3
OUT_EVERY = 5          # keep every 5th forecast step (30 days) in the file; the page interpolates
ROOT = Path(__file__).resolve().parents[2]
d_ = lambda s: date(int(s[:4]), int(s[5:7]), int(s[8:10]))


def inside(lon, lat, ring):
    c = False
    for i in range(len(ring)):
        x1, y1 = ring[i - 1]; x2, y2 = ring[i]
        if (y2 > lat) != (y1 > lat) and lon < (x1 - x2) * (lat - y2) / (y1 - y2) + x2:
            c = not c
    return c


def cells_for(pfile, ring, since=None):
    d = json.loads(pfile.read_text())
    dates = d["dates"]; keep = [i for i, x in enumerate(dates) if since is None or x >= since]
    lat0 = sum(p[1] for p in ring) / len(ring)
    mx, my = 111320 * math.cos(math.radians(lat0)), 110540
    groups = {}
    for i, (lo, la) in enumerate(zip(d["lon"], d["lat"])):
        if not inside(lo, la, ring):
            continue
        groups.setdefault((int(lo * mx // CELL_M), int(la * my // CELL_M)), []).append(i)
    out = []
    for (cx, cy), idx in groups.items():
        if len(idx) < MIN_PTS:
            continue
        ser = []
        for k in keep:
            v = [d["change"][k][i] for i in idx if d["change"][k][i] is not None]
            ser.append(float(np.median(v)) * d["scale"] if len(v) >= MIN_PTS else None)
        pts = [(dates[k], v) for k, v in zip(keep, ser) if v is not None]
        if len(pts) < 8:
            continue
        v0 = pts[0][1]
        out.append(dict(lon=round((cx + 0.5) * CELL_M / mx, 5), lat=round((cy + 0.5) * CELL_M / my, 5), n=len(idx),
                        dates=[p[0] for p in pts], mm=[p[1] - v0 for p in pts]))
    return out


def run(pipe, series, horizon_days):
    """series: list of (dates, mm). Returns per series (grid times, median, q10, q90) in mm, absolute, after the last date."""
    ctx, meta = [], []
    for ds, mm in series:
        t0 = d_(ds[0]); td = np.array([(d_(x) - t0).days for x in ds], float); y = np.array(mm)
        grid = np.arange(0, td[-1] + 1, STEP); yg = np.interp(grid, td, y)
        ctx.append((yg - yg[-1]).astype(np.float32)); meta.append((t0, td[-1], yg[-1]))
    steps = max(1, max(math.ceil(h / STEP) for h in horizon_days))
    out = []
    for i in range(0, len(ctx), 64):
        q, _ = pipe.predict_quantiles(ctx[i:i + 64], prediction_length=steps, quantile_levels=Q)
        for j, qq in enumerate(q):
            a = qq[0].numpy(); t0, tl, yl = meta[i + j]
            out.append((t0, tl, yl + a[:, 1], yl + a[:, 0], yl + a[:, 2]))
    return out


def main():
    prod = Path(sys.argv[1])
    ring = json.loads((ROOT / "app/ocnele_mari_boundary.geojson").read_text())
    ring = (ring["features"][0] if "features" in ring else ring)["geometry"]["coordinates"][0]
    from chronos import Chronos2Pipeline
    pipe = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
    sets = {"s1:029A": (prod / "s1/all/points_029A.json", None), "s1:007D": (prod / "s1/jul_nov/points_007D.json", None),   # the long window keeps only 8 town points on 007D (winter)
            "nisar:129A": (prod / "nisar/points_129A.json", "2026-06-01"), "nisar:094D": (prod / "nisar/points_094D.json", "2026-06-01")}
    res = dict(model="amazon/chronos-2 (zero-shot)", end=END.isoformat(), cell_m=CELL_M, step_days=STEP * OUT_EVERY,
               note="Chronos-2 per 240 m cell of measured points inside the town boundary; mm since the series' first date.",
               tracks={})
    for key, (pf, since) in sets.items():
        if not pf.exists():
            continue
        cells = cells_for(pf, ring, since)
        if not cells:
            continue
        # forecast to END from each cell's last date
        hz = [(END - d_(c["dates"][-1])).days for c in cells]
        fc = run(pipe, [(c["dates"], c["mm"]) for c in cells], hz)
        # backtest: the last 60 days, from the data before them
        bt_err, nc_err = [], []
        bt_in = [(c, [i for i, x in enumerate(c["dates"]) if (d_(c["dates"][-1]) - d_(x)).days > 60]) for c in cells]
        bt_in = [(c, k) for c, k in bt_in if len(k) >= 8 and len(c["dates"]) - len(k) >= 2]
        if bt_in:
            bf = run(pipe, [([c["dates"][i] for i in k], [c["mm"][i] for i in k]) for c, k in bt_in], [61])
            for (c, k), (t0, tl, med, _, _) in zip(bt_in, bf):
                held = [(d_(x) - t0).days for x in c["dates"][len(k):]]; hv = np.array(c["mm"][len(k):])
                fx = tl + STEP * (np.arange(len(med)) + 1)
                bt_err.append(float(np.mean(np.abs(np.interp(held, fx, med) - hv))))
                nc_err.append(float(np.mean(np.abs(c["mm"][len(k) - 1] - hv))))
        out = []
        for c, (t0, tl, med, lo, hi) in zip(cells, fc):
            n = math.ceil(((END - t0).days - tl) / STEP)
            sel = list(range(OUT_EVERY - 1, n, OUT_EVERY)) + ([n - 1] if (n - 1) % OUT_EVERY != OUT_EVERY - 1 else [])
            out.append(dict(lon=c["lon"], lat=c["lat"], n=c["n"], obs_dates=c["dates"], obs=[round(v, 1) for v in c["mm"]],
                            dates=[(t0 + timedelta(days=float(tl + STEP * (i + 1)))).isoformat() for i in sel],
                            median=[round(float(med[i]), 1) for i in sel], q10=[round(float(lo[i]), 1) for i in sel],
                            q90=[round(float(hi[i]), 1) for i in sel]))
        bt = dict(days=60, cells=len(bt_err), mae_chronos=round(float(np.median(bt_err)), 2),
                  mae_no_change=round(float(np.median(nc_err)), 2),
                  chronos_better_share=round(float(np.mean(np.array(bt_err) < np.array(nc_err))), 2)) if bt_err else None
        res["tracks"][key] = dict(cells=out, backtest=bt, window=str(pf.parent.relative_to(prod)))
        print(key, f"{len(out)} cells, {sum(c['n'] for c in out)} points", "backtest", bt)
    (prod / "forecast_area.json").write_text(json.dumps(res, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
