# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Zero-shot Chronos-2 forecasts to 1 January 2029 for every zone and track that has a series, for the page's menu.

    python forecast_zones.py ../../products/ocnele_mari    (environment with chronos-forecasting >= 2, CPU torch)

The same model and settings as forecast_chronos.py (zero-shot, 6-day steps, 80 % interval), applied to each zone's
baseline series: Sentinel-1 from sensitivity.json (the window with the most dates per track), NISAR from series.json
(only the dates after the January to June gap, re-zeroed at the first, because the series restarts there). Fine-tuning
was tested and rejected (notebooks/03/chronos_finetune_test.json). Only Zone 4 on 029A has a backtest; the others reuse
the method without their own test, and the page says so. Writes <products>/forecast_zones.json.
"""
import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

END, STEP, Q = date(2029, 1, 1), 6.0, [0.1, 0.5, 0.9]
d_ = lambda s: date(int(s[:4]), int(s[5:7]), int(s[8:10]))


def series_sets(prod):
    sens = json.loads((prod / "sensitivity.json").read_text())
    ser = json.loads((prod / "series.json").read_text())
    out = []
    for w in sens["windows"].values():
        for trk, v in w["variants"].items():
            for zid, e in v.get("baseline", {}).items():
                if zid.startswith("z") and e:
                    out.append(("s1", trk, zid, e["dates"], e["mm"]))
    for p in ser:
        if not p["id"].startswith("z"):
            continue
        for key, e in p["series"].items():
            if key.startswith("nisar:"):
                pts = [(d, v) for d, v in zip(e["dates"], e["mm"]) if d >= "2026-06-01" and v is not None]
                if pts:
                    out.append(("nisar", key.split(":")[1], p["id"], [d for d, _ in pts], [v - pts[0][1] for _, v in pts]))
    best = {}
    for s in out:   # keep the longest series per (sensor, track, zone)
        k = s[:3]
        if k not in best or len(s[3]) > len(best[k][3]):
            best[k] = s
    return list(best.values())


def main():
    prod = Path(sys.argv[1])
    from chronos import Chronos2Pipeline
    pipe = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
    res = {}
    for sat, trk, zid, dates, mm in series_sets(prod):
        pts = [(d_(d), v) for d, v in zip(dates, mm) if v is not None]
        if len(pts) < 8:
            continue
        t0 = pts[0][0]; td = np.array([(d - t0).days for d, _ in pts], float); y = np.array([v for _, v in pts])
        grid = np.arange(0, td[-1] + 1, STEP); yg = np.interp(grid, td, y)
        last = t0 + timedelta(days=float(td[-1]))
        steps = math.ceil((END - last).days / STEP)
        # backtest: forecast the last 60 days from the data before them; score against the measured values and
        # against the simplest guess (no further change). Same model and settings as the forecast itself.
        bt = None
        cut = td[-1] - 60
        if (td <= cut).sum() >= 8 and (td > cut).sum() >= 2:
            gb = grid[grid <= cut]; yb = np.interp(gb, td, y)
            hb = math.ceil((td[-1] - gb[-1]) / STEP)
            qb, _ = pipe.predict_quantiles([(yb - yb[-1]).astype(np.float32)], prediction_length=hb, quantile_levels=Q)
            mb = qb[0][0].numpy()[:, 1] + yb[-1]
            fx = gb[-1] + STEP * (np.arange(hb) + 1)
            held = td > cut
            pred = np.interp(td[held], fx, mb)
            bt = dict(days=60, n=int(held.sum()), mae_chronos=round(float(np.mean(np.abs(pred - y[held]))), 2),
                      mae_no_change=round(float(np.mean(np.abs(yb[-1] - y[held]))), 2))
        q, _ = pipe.predict_quantiles([(yg - yg[-1]).astype(np.float32)], prediction_length=steps, quantile_levels=Q)
        q = q[0][0].numpy()
        fd = [(last + timedelta(days=STEP * (k + 1))).isoformat() for k in range(steps)]
        res.setdefault(zid, {})[f"{sat}:{trk}"] = dict(
            observed_dates=[d.isoformat() for d, _ in pts], observed_mm=[round(float(v), 2) for _, v in pts],
            dates=fd, median=[round(float(y[-1] + v), 2) for v in q[:, 1]],
            q10=[round(float(y[-1] + v), 2) for v in q[:, 0]], q90=[round(float(y[-1] + v), 2) for v in q[:, 2]],
            backtested=bt is not None, backtest=bt)
        print(zid, sat, trk, f"{len(pts)} dates → {END} median {y[-1] + q[-1, 1]:+.1f} mm", f"backtest {bt}")
    (prod / "forecast_zones.json").write_text(json.dumps(dict(model="amazon/chronos-2 (zero-shot)", end=END.isoformat(),
        level=0.8, note="Each series is backtested on its last 60 days (backtest: mean error of Chronos-2 and of a no-change guess, mm).",
        zones=res), indent=1) + "\n")


if __name__ == "__main__":
    main()
