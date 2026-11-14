# Owner: 05 · Validator (Paul)
# Exploration only (never imported). Run after notebooks/05/soil_moisture.py:
#   python notebooks/05/sm_vs_s1.py
# Compares Sentinel-1 zone displacement with NISAR soil moisture and ERA5 rainfall on matching dates.
"""Does the Sentinel-1 displacement follow soil moisture or rain?

Sentinel-1 zone displacement (sentinel1/analysis/summary.json, baseline fit) is already relative to the 3 to 6.5 km
reference band, so the moisture that matters is the zone minus that band. For each track and area (z1 to z4, and the
outer control ring, which is stable ground: a moisture effect there cannot be subsidence):
  1. match every NISAR moisture date to the nearest Sentinel-1 date (at most 2 days apart);
  2. remove a straight line from the displacement (the trend we want to keep);
  3. correlate what is left, one input at a time, with: moisture (area minus band), the same moisture one date
     earlier (lag), and the 7- and 30-day ERA5 rain totals before the Sentinel-1 date (Pearson r);
  4. for moisture, also fit mm per 0.01 m3/m3.
With 5 to 12 points per series, only |r| above about 0.6 to 0.8 means anything; this is a screen, not a proof.
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import common as C  # noqa: E402

MAX_DAYS = 2
SM = C.WORK / "ocnele_mari" / "sm"


def r_crit(n: int) -> float:
    """|r| needed for p < 0.05 (two-sided) with n points."""
    from scipy import stats
    t = stats.t.ppf(0.975, n - 2)
    return float(t / np.sqrt(n - 2 + t * t))


def rain_totals():
    with open(SM / "rain_era5_daily.csv", encoding="utf-8") as f:
        rain = {r["date"]: float(r["precip_mm"]) for r in csv.DictReader(f) if r["precip_mm"]}
    def total(day: np.datetime64, n: int) -> float:
        return sum(rain.get(str(day - np.timedelta64(k, 'D')), 0.0) for k in range(n))
    return total


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # --all-pixels: sensitivity run that also uses the retrievals NISAR does not recommend (labelled as such)
    every = "--all-pixels" in sys.argv
    sfx = "_sm_all" if every else "_sm"
    with open(SM / "sm_zones.csv", encoding="utf-8") as f:
        sm = []
        for r in csv.DictReader(f):
            if every:   # read the *_sm_all columns through the same names as the recommended run
                r = {**r, **{k[:-4]: v for k, v in r.items() if k.endswith(sfx)}}
            if r.get("ref_band_sm"):
                sm.append(r)
        sm.sort(key=lambda r: r["date"])
    s1 = json.loads((ROOT / "sentinel1/analysis/summary.json").read_text(encoding="utf-8"))
    rain = rain_totals()
    areas = [(z["id"], f"zone_{i}") for i, z in enumerate(C.SITES["ocnele_mari"]["zones"], start=1)]
    areas.append(("control", "outer_control"))
    result, fig_rows = {}, []
    for track in ("029A", "007D"):
        dates = np.array([np.datetime64(f"{d[:4]}-{d[4:6]}-{d[6:]}") for d in s1[track]["dates"]])
        base = s1[track]["fits"]["baseline"]
        for area, key in areas:
            name = f"{track} {area}"
            if key not in base or not base[key].get("pixels"):
                result[name] = dict(note="no Sentinel-1 series")
                continue
            disp = np.array(base[key]["displacement_mm"], float)
            rows, prev = [], None
            for r in sm:
                if not r.get(f"{area}_sm"):
                    prev = None
                    continue
                w = float(r[f"{area}_sm"]) - float(r["ref_band_sm"])
                day = np.datetime64(r["date"])
                j = int(np.argmin(np.abs(dates - day)))
                if abs((dates[j] - day).astype(int)) <= MAX_DAYS and np.isfinite(disp[j]):
                    rows.append(dict(date=r["date"], t=(dates[j] - dates[0]).astype(int) / 365.25, d=disp[j], w=w,
                                     w_lag=prev, rain7=rain(dates[j], 7), rain30=rain(dates[j], 30)))
                prev = w
            if len(rows) < 5:
                result[name] = dict(points=len(rows), note="fewer than 5 matched dates")
                continue
            t, d = np.array([x["t"] for x in rows]), np.array([x["d"] for x in rows])
            trend = np.polyfit(t, d, 1)
            resid = d - np.polyval(trend, t)
            out = dict(points=len(rows), r_needed_p05=round(r_crit(len(rows)), 2), dates=[x["date"] for x in rows],
                       trend_mm_yr=round(float(trend[0]), 1), resid_scatter_mm=round(float(resid.std()), 2))
            for k in ("w", "w_lag", "rain7", "rain30"):
                pairs = [(res, x[k]) for res, x in zip(resid, rows) if x[k] is not None]
                if len(pairs) >= 5:
                    a, b = map(np.array, zip(*pairs))
                    out[f"r_{k}"] = round(float(np.corrcoef(a, b)[0, 1]), 2) if b.std() > 0 else None
            w = np.array([x["w"] for x in rows])
            out["moisture_range_pct"] = round(100 * float(w.max() - w.min()), 2)
            out["mm_per_1pct_moisture"] = round(float(np.polyfit((w - w.mean()) * 100, resid, 1)[0]), 2) if w.std() else None
            result[name] = out
            fig_rows.append((track, area, rows))

    tag = "_all_pixels" if every else ""
    C.save_json(SM / f"sm_vs_s1{tag}.json", result)
    for k, v in result.items():
        print(f"{k:13s}", {a: b for a, b in v.items() if a != "dates"})

    if fig_rows:
        names = [a for a, _ in areas]
        fig, axes = plt.subplots(len(names), 1, figsize=(9, 2.2 * len(names)), sharex=True, constrained_layout=True)
        for ax, area in zip(axes, names):
            ax2 = ax.twinx()
            for track, a, rows in fig_rows:
                if a != area:
                    continue
                x = np.array([r["date"] for r in rows], dtype="datetime64[D]")
                ax.plot(x, [r["d"] for r in rows], "o-", ms=3, label=f"S1 {track} displacement")
                ax2.plot(x, [100 * r["w"] for r in rows], "s--", ms=3, alpha=0.7,
                         color="tab:green" if track == "029A" else "tab:olive", label=f"moisture minus band ({track} dates)")
            ax.set_ylabel(f"{area}\nLOS mm")
            ax2.set_ylabel("Δ moisture, %")
            ax.axhline(0, color="grey", lw=0.5)
            ax.legend(loc="upper left", fontsize=7)
            ax2.legend(loc="upper right", fontsize=7)
        fig.suptitle("Sentinel-1 displacement vs NISAR soil moisture (area minus reference band), Jul to Oct 2026", fontsize=10)
        if not every:
            fig.savefig(C.DOCS / "figures" / "05_soil_moisture_vs_s1.png", dpi=100)
    print(f"→ {SM / ('sm_vs_s1' + tag + '.json')}")


if __name__ == "__main__":
    main()
