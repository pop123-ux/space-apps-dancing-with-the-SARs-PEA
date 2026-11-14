# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Exploration only (never imported). Does fine-tuning Chronos-2 on our own radar series beat zero-shot? A predeclared test.

    python notebooks/03/chronos_finetune_test.py   (environment with chronos-forecasting >= 2, CPU torch; about 15 min)

Rule (DECISIONS.md, 15 Nov 2026, written before the run): adopt fine-tuning only if it lowers Zone 4's MAE at both the
30- and 88-day horizons on the test cutoffs AND its 80 % interval still holds 70 to 90 % of the truths. Otherwise the
page keeps zero-shot Chronos-2.

Data, split in time so the test never trains on what it forecasts:
  train  Sentinel-1 January to October pixel series (029A and 007D, sentinel1/assets_jan_oct), every pixel with all
         49 dates, Zone 4 and 300 m around it excluded, cut at TRAIN_END (only dates up to 30 June 2026 are used)
  test   Zone 4 029A series (sentinel1/analysis_jan_oct/summary.json), forecasts issued at cutoffs after TRAIN_END,
         30 and 88 days ahead, exactly as forecast_chronos.py's January to October backtest
Fine-tuning: LoRA (the pretrained weights stay frozen; only small adapters learn), few steps, small learning rate.
Writes notebooks/03/chronos_finetune_test.json.
"""
import json
import math
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402

import common as C  # noqa: E402
import export  # noqa: E402

TRAIN_END = "20260630"
STEP, Q = 6.0, [0.1, 0.5, 0.9]
N_PIX, STEPS, LR = 3000, 300, 1e-4


def pixel_series():
    out = []
    rng = np.random.default_rng(2026)
    for trk in ("029A", "007D"):
        z = export.load_grid(trk, "jan_oct")
        d = z["displacement_mm"]; dates = [str(x) for x in z["dates"]]
        k = sum(1 for x in dates if x <= TRAIN_END)
        xmin, ymin, xmax, ymax = z["bounds_utm"]; ny, nx = d.shape[1:]
        X = xmin + (np.arange(nx) + .5) * (xmax - xmin) / nx; Y = ymax - (np.arange(ny) + .5) * (ymax - ymin) / ny
        XX, YY = np.meshgrid(X, Y)
        z4 = next(q for q in C.SITES["ocnele_mari"]["zones"] if q["id"] == "z4")
        zx, zy = C.to_xy(32635, z4["lon"], z4["lat"])
        ok = np.isfinite(d).all(0) & (np.hypot(XX - zx, YY - zy) > z4["r_m"] + 300)
        ii, jj = np.nonzero(ok)
        pick = rng.choice(len(ii), size=min(N_PIX // 2, len(ii)), replace=False)
        for p in pick:
            y = d[:k, ii[p], jj[p]].astype(np.float32)
            out.append(y - y[-1])
    return out


def backtest(pipe):
    s = json.loads((ROOT / "sentinel1/analysis_jan_oct/summary.json").read_text())["029A"]
    yd = np.array(s["fits"]["baseline"]["zone_4"]["displacement_mm"])
    dts = [date(int(x[:4]), int(x[4:6]), int(x[6:])) for x in s["dates"]]
    td = np.array([(d - dts[0]).days for d in dts], float)
    grid = np.arange(0, td[-1] + 1, STEP); yg = np.interp(grid, td, yd)
    t_end = (date(int(TRAIN_END[:4]), int(TRAIN_END[4:6]), int(TRAIN_END[6:])) - dts[0]).days
    res = {}
    for H in (30, 88):
        e, c = [], []
        for i in range(10, len(grid)):
            if grid[i] <= t_end or grid[i] + H > td[-1]:
                continue
            steps = math.ceil(H / STEP)
            q, _ = pipe.predict_quantiles([(yg[:i + 1] - yg[i]).astype(np.float32)], prediction_length=steps, quantile_levels=Q)
            q = q[0][0].numpy(); xs = np.r_[0, np.arange(1, steps + 1) * STEP]
            lo, m, hi = (float(np.interp(H, xs, np.r_[0, q[:, j]])) for j in range(3))
            truth = float(np.interp(grid[i] + H, td, yd) - yg[i])
            e.append(abs(truth - m)); c.append(lo <= truth <= hi)
        res[f"{H}d"] = dict(n=len(e), mae_mm=round(float(np.mean(e)), 3) if e else None,
                            interval80_coverage=round(float(np.mean(c)), 3) if c else None)
    return res


def main():
    from chronos import Chronos2Pipeline
    base = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
    zero = backtest(base)
    print("zero-shot", zero, flush=True)
    train = pixel_series()
    print(f"training on {len(train)} pixel series (dates to {TRAIN_END}), LoRA, {STEPS} steps", flush=True)
    tuned = base.fit(train, prediction_length=math.ceil(88 / STEP), finetune_mode="lora", learning_rate=LR,
                     num_steps=STEPS, batch_size=64, output_dir=str(ROOT / "data" / "work" / "chronos_ft"),
                     remove_printer_callback=True)
    ft = backtest(tuned)
    print("fine-tuned", ft, flush=True)
    better = all(ft[h]["mae_mm"] is not None and zero[h]["mae_mm"] is not None and ft[h]["mae_mm"] < zero[h]["mae_mm"] for h in ("30d", "88d"))
    calibrated = all(ft[h]["interval80_coverage"] is not None and 0.7 <= ft[h]["interval80_coverage"] <= 0.9 for h in ("30d", "88d"))
    out = dict(rule="adopt only if MAE drops at 30 and 88 days and 80 % coverage stays within 0.7 to 0.9",
               train=dict(series=len(train), tracks=["029A", "007D"], dates_until=TRAIN_END, zone4_excluded=True,
                          mode="lora", steps=STEPS, learning_rate=LR),
               test="Zone 4 029A, cutoffs after the training end", zero_shot=zero, fine_tuned=ft,
               adopt=bool(better and calibrated))
    (ROOT / "notebooks" / "03" / "chronos_finetune_test.json").write_text(json.dumps(out, indent=1) + "\n")
    print("adopt fine-tuning:", out["adopt"])


if __name__ == "__main__":
    main()
