# Owner: 05 · Validator (Paul)
# Exploration only (never imported). Run after notebooks/05/soil_moisture.py, from the repo root:
#   python notebooks/05/z4_screen.py <forecast.json from r06/page>
# Part 1: date-aligned Zone 4 and control-ring inputs (Sentinel-1 LOS, NISAR moisture, ERA5 rain) and the screen.
# Part 2: the predeclared rain test against the forecast baselines (docs/validation-log.md, "Predeclared ...").
"""Zone 4 + control screen and the predeclared 7-day-rain forecast test.

Screen inputs per Sentinel-1 date (sentinel1/analysis/summary.json, baseline fit, LOS mm, positive towards the
satellite, relative to the 3 to 6.5 km reference band, first date = 0):
  moisture  NISAR L3 SME2 (m3/m3) on the nearest date at most 2 days away, area minus reference band;
            "rec" = recommended retrievals only, "all" = every retrieval (sensitivity, not recommended by NISAR)
  lag1      the same moisture on the previous NISAR date (about 3 to 9 days earlier)
  rain7/30  ERA5 precipitation summed over the 7 / 30 days ending on the Sentinel-1 date (mm)
Correlations are Pearson r, raw and after removing a straight line in time, with the |r| needed for p < 0.05 and the
range of r when any one date is left out. They are screening flags only: dates are serially dependent and several
inputs are tried, so chance associations look stronger than they are.
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

import numpy as np
from scipy import stats
from scipy.linalg import cho_factor, cho_solve
from scipy.stats import theilslopes

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import common as C  # noqa: E402

SM = C.WORK / "ocnele_mari" / "sm"
MAX_DAYS = 2
LAMBDA = 1.0   # predeclared ridge penalty on the standardised rain input; not tuned


# ------------------------------------------------------------------ inputs
def rain_series():
    with open(SM / "rain_era5_daily.csv", encoding="utf-8") as f:
        rain = {r["date"]: float(r["precip_mm"]) for r in csv.DictReader(f) if r["precip_mm"]}
    def total(day, n):
        return float(sum(rain[str(np.datetime64(day) - np.timedelta64(k, "D"))] for k in range(n)))
    return total


def moisture_rows():
    with open(SM / "sm_zones.csv", encoding="utf-8") as f:
        return sorted(csv.DictReader(f), key=lambda r: r["date"])


def f(x):
    return float(x) if x not in (None, "") else None


def aligned(track: str, area: str, key: str):
    s1 = json.loads((ROOT / "sentinel1/analysis/summary.json").read_text(encoding="utf-8"))
    dates = [f"{d[:4]}-{d[4:6]}-{d[6:]}" for d in s1[track]["dates"]]
    fit = s1[track]["fits"]["baseline"].get(key, {})
    los = fit.get("displacement_mm") or [None] * len(dates)
    sm = moisture_rows()
    rain = rain_series()
    out = []
    for d, y in zip(dates, los):
        day = np.datetime64(d)
        cand = [r for r in sm if abs((np.datetime64(r["date"]) - day).astype(int)) <= MAX_DAYS]
        r = min(cand, key=lambda r: abs((np.datetime64(r["date"]) - day).astype(int))) if cand else None
        prev = None
        if r:
            earlier = [x for x in sm if x["date"] < r["date"]]
            prev = earlier[-1] if earlier else None
        row = dict(date=d, track=track, area=area, los_mm=None if y is None else round(float(y), 2),
                   s1_pixels=fit.get("pixels", 0), rain7_mm=round(rain(d, 7), 1), rain30_mm=round(rain(d, 30), 1),
                   nisar_date=r["date"] if r else None, nisar_track=r["track"] if r else None)
        for q, tag in (("_sm", "rec"), ("_sm_all", "all")):
            a, b = (f(r.get(f"{area}{q}")), f(r.get(f"ref_band{q}"))) if r else (None, None)
            row[f"moist_{tag}"] = None if a is None or b is None else round(a - b, 4)
            row[f"moist_{tag}_px"] = int(r.get(f"{area}_n" if tag == "rec" else f"{area}_n_all") or 0) if r else 0
            pa, pb = (f(prev.get(f"{area}{q}")), f(prev.get(f"ref_band{q}"))) if prev else (None, None)
            row[f"lag1_{tag}"] = None if pa is None or pb is None else round(pa - pb, 4)
        out.append(row)
    return out


# ------------------------------------------------------------------ screen
def screen(rows, feature):
    pts = [(r["date"], r["los_mm"], r[feature]) for r in rows if r["los_mm"] is not None and r[feature] is not None]
    n = len(pts)
    if n < 5:
        return dict(feature=feature, n=n, note="fewer than 5 dates with both values")
    t = np.array([(np.datetime64(d) - np.datetime64(pts[0][0])).astype(int) for d, _, _ in pts], float)
    y = np.array([p[1] for p in pts])
    x = np.array([p[2] for p in pts])
    if x.std() == 0:
        return dict(feature=feature, n=n, note="input does not vary")
    yd = y - np.polyval(np.polyfit(t, y, 1), t)
    crit = float(stats.t.ppf(0.975, n - 2) / np.sqrt(n - 2 + stats.t.ppf(0.975, n - 2) ** 2))
    def r(a, b):
        return float(np.corrcoef(a, b)[0, 1])
    loo = []
    for i in range(n):
        k = np.arange(n) != i
        yk = y[k] - np.polyval(np.polyfit(t[k], y[k], 1), t[k])
        loo.append(r(yk, x[k]))
    r_raw, r_det = r(y, x), r(yd, x)
    crit_loo = float(stats.t.ppf(0.975, n - 3) / np.sqrt(n - 3 + stats.t.ppf(0.975, n - 3) ** 2))
    flag = abs(r_det) >= crit
    robust = all(abs(v) >= crit_loo for v in loo) and all(np.sign(v) == np.sign(r_det) for v in loo)
    return dict(feature=feature, n=n, r_raw=round(r_raw, 2), r_detrended=round(r_det, 2), r_needed=round(crit, 2),
                loo_min=round(min(loo), 2), loo_max=round(max(loo), 2),
                verdict=("candidate, survives leaving out any date" if flag and robust else
                         "candidate, but one date decides it" if flag else "no flag"))


# ------------------------------------------------------------------ forecast test
def baselines(t, y, ahead):
    """Persistence, Theil-Sen and the Matern 3/2 GP, copied from forecast.py on r06/page (owner 03) to score on the
    same inputs; unchanged except for formatting."""
    slope = float(theilslopes(y, t).slope)
    a = np.asarray(ahead, float)
    drift = slope * a
    residual = y - slope * t
    residual = residual - np.median(residual)
    def kernel(x, z, length, signal):
        d = np.sqrt(3) * np.abs(x[:, None] - z[None, :]) / length
        return signal ** 2 * (1 + d) * np.exp(-d)
    best = None
    scale = max(float(np.std(residual)), .25)
    for length in (6., 12., 24.):
        for signal in (scale * .5, scale):
            for noise in (scale * .25, scale * .5, scale):
                cov = kernel(t, t, length, signal) + np.eye(t.size) * (noise ** 2 + 1e-9)
                ch = cho_factor(cov)
                alpha = cho_solve(ch, residual)
                loss = .5 * (residual @ alpha) + np.log(np.diag(ch[0])).sum()
                if best is None or loss < best[0]:
                    best = (loss, length, signal, alpha)
    _, length, signal, alpha = best
    mean = kernel(np.r_[0., a], t, length, signal) @ alpha
    return dict(persistence=np.zeros_like(a), theil_sen=drift, gaussian_process=drift + mean[1:] - mean[0])


def rain_model(t, y, x_train, x_now, x_future, ahead):
    """Predeclared: Theil-Sen trend, then ridge (lambda fixed) of the detrended LOS on standardised rain, all fitted
    inside the cutoff. Issuance assumes rain returns to its training mean; conditional uses the observed future rain."""
    slope = float(theilslopes(y, t).slope)
    res = y - slope * t
    res = res - res.mean()
    mu, sd = x_train.mean(), x_train.std() or 1.0
    z = (x_train - mu) / sd
    beta = float(z @ res / (z @ z + LAMBDA))          # mm per standard deviation of 7-day rain
    a = np.asarray(ahead, float)
    issuance = slope * a + beta * (0.0 - (x_now - mu) / sd)
    conditional = slope * a + beta * ((np.asarray(x_future) - mu) / sd - (x_now - mu) / sd)
    return issuance, conditional, beta


def backtest(fc):
    rain = rain_series()
    dates = fc["training_dates"]
    obs = np.array(fc["observed_mm"], float)
    out, scores = [], {k: [] for k in ("persistence", "theil_sen", "gaussian_process", "rain_issuance",
                                       "rain_conditional")}
    for fold in fc["folds"]:
        n = dates.index(fold["origin"]) + 1
        tr = np.array([(np.datetime64(d) - np.datetime64(fold["origin"])).astype(int) for d in dates[:n]], float)
        y = obs[:n] - obs[n - 1]                       # relative to the cutoff, like forecast.py
        lead = fold["lead_days"]
        xt = np.array([rain(d, 7) for d in dates[:n]])
        fut = [rain(str(np.datetime64(fold["origin"]) + np.timedelta64(h, "D")), 7) for h in lead]
        base = baselines(tr, y, lead)
        iss, cond, beta = rain_model(tr, y, xt, xt[-1], fut, lead)
        truth = fold["observed_mm"][-1]
        row = dict(origin=fold["origin"], lead_days=lead[-1], observed_mm=round(truth, 2), beta_mm_per_sd=round(beta, 2),
                   rain7_at_cutoff=round(xt[-1], 1), rain7_at_target=round(fut[-1], 1),
                   export=dict((k, round(v[-1], 2)) for k, v in fold["predicted_mm"].items()),
                   reproduced=dict((k, round(float(v[-1]), 2)) for k, v in base.items()),
                   rain_issuance=round(float(iss[-1]), 2), rain_conditional=round(float(cond[-1]), 2))
        for k in ("persistence", "theil_sen", "gaussian_process"):
            scores[k].append(abs(truth - float(base[k][-1])))
        scores["rain_issuance"].append(abs(truth - float(iss[-1])))
        scores["rain_conditional"].append(abs(truth - float(cond[-1])))
        out.append(row)
    mae = {k: round(float(np.mean(v)), 2) for k, v in scores.items()}
    return out, mae


def main():
    fc_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    report = {}
    for track in ("029A", "007D"):
        for area, key in (("z4", "zone_4"), ("control", "outer_control")):
            rows = aligned(track, area, key)
            report[f"{track} {area}"] = dict(
                rows=rows,
                screen=[screen(rows, k) for k in ("moist_rec", "moist_all", "lag1_rec", "lag1_all", "rain7_mm",
                                                  "rain30_mm")])
    if fc_path:
        fc = json.loads(fc_path.read_text(encoding="utf-8"))
        folds, mae = backtest(fc)
        report["forecast_test"] = dict(source=str(fc_path), folds=folds, mae_30d_mm=mae,
                                       export_mae_30d_mm={k: round(v["mae_mm"], 2) for k, v in fc["metrics"].items()})
    C.save_json(SM / "z4_screen.json", report)

    # handoff for 03 (docs/forecast.md, "Paul / 05 handoff"): small derived tables, committed next to this script
    here = pathlib.Path(__file__).resolve().parent
    cols = ["date", "track", "area", "los_mm", "s1_pixels", "nisar_date", "nisar_track",
            "moist_rec", "moist_rec_px", "moist_all", "moist_all_px", "lag1_rec", "lag1_all", "rain7_mm", "rain30_mm"]
    with open(here / "z4_screen_inputs.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for k, v in report.items():
            if "rows" in v:
                w.writerows({c: ("" if r.get(c) is None else r.get(c)) for c in cols} for r in v["rows"])
    slim = {k: (v["screen"] if "screen" in v else {kk: vv for kk, vv in v.items() if kk != "source"})
            for k, v in report.items()}
    (here / "z4_screen_results.json").write_text(json.dumps(slim, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: (v["screen"] if "screen" in v else {kk: vv for kk, vv in v.items() if kk != "source"})
                      for k, v in report.items()}, indent=1, default=str))


if __name__ == "__main__":
    main()
