# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Does weather (rain, soil moisture) help Chronos-2 forecast Zone 4? A predeclared backtest.

    python chronos_weather.py ../analysis_jan_oct/summary.json -o ../analysis/chronos_weather.json

Target: the January to October 029A Zone 4 baseline series (cumulative LOS, mm), resampled to 6-day steps, as in
forecast_chronos.py. Covariates, at each 6-day step, from the Open-Meteo archive at Ocnele Mari (ERA5 / ERA5-Land):
  rain6   precipitation over the 6 days ending at the step (mm)
  rain30  precipitation over the 30 days ending at the step (mm)
  sm      mean 0 to 7 cm soil moisture over the 6 days ending at the step (m3/m3)
05's NISAR SME2 soil moisture (notebooks/05) covers only the summer dates, so it cannot drive the 54 January to October
cutoffs; ERA5-Land is the full-year substitute, at about 9 km instead of 200 m.

Variants, all on the same cutoffs and horizons (30 and 88 days):
  none      the target alone (the current chronos2 path)
  past      rain6, rain30, sm as past-only covariates: usable for the January forecast
  oracle    the same, plus their real values after the cutoff as known-future covariates: a diagnostic upper bound
            (no January forecast can know the weather of December)

Predeclared rule (DECISIONS.md, 14 Nov 20:30, written before the first run): `past` replaces `none` in the export only if
it lowers the MAE at both 30 and 88 days. The same caveats as forecast_chronos.py apply: overlapping cutoffs, one zone,
one track, truths read off the final reconstruction.
"""
import argparse
import json
import math
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.request import urlopen

import numpy as np

LAT, LON = 45.088, 24.290
STEP = 6.0
Q = [0.1, 0.5, 0.9]
API = 'https://archive-api.open-meteo.com/v1/archive'


def weather(start, end, tries=5):
    """Daily precipitation (mm) and daily-mean 0 to 7 cm soil moisture (m3/m3), keyed by ISO day."""
    url = (f'{API}?latitude={LAT}&longitude={LON}&start_date={start}&end_date={end}'
           '&daily=precipitation_sum&hourly=soil_moisture_0_to_7cm&timezone=UTC')
    for k in range(tries):
        try:
            with urlopen(url, timeout=120) as r:
                w = json.load(r)
            break
        except OSError:
            if k == tries - 1:
                raise
            time.sleep(2 ** k)
    rain = dict(zip(w['daily']['time'], w['daily']['precipitation_sum']))
    sm = {}
    for t, v in zip(w['hourly']['time'], w['hourly']['soil_moisture_0_to_7cm']):
        if v is not None:
            sm.setdefault(t[:10], []).append(v)
    return rain, {d: float(np.mean(v)) for d, v in sm.items()}


def covariates(days, rain, sm):
    """rain6, rain30, sm at each date in days (datetime.date)."""
    def total(d, n):
        return float(sum(rain.get((d - timedelta(days=k)).isoformat()) or 0.0 for k in range(n)))
    def mean_sm(d):
        v = [sm[x] for x in ((d - timedelta(days=k)).isoformat() for k in range(6)) if x in sm]
        return float(np.mean(v)) if v else np.nan
    out = dict(rain6=[total(d, 6) for d in days], rain30=[total(d, 30) for d in days], sm=[mean_sm(d) for d in days])
    return {k: np.asarray(v, np.float32) for k, v in out.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('janoct', type=Path)
    ap.add_argument('-o', '--output', type=Path, required=True)
    a = ap.parse_args()
    s = json.loads(a.janoct.read_text())['029A']
    yd = np.array(s['fits']['baseline']['zone_4']['displacement_mm'])
    dates = [date(int(x[:4]), int(x[4:6]), int(x[6:])) for x in s['dates']]
    td = np.array([(d - dates[0]).days for d in dates], float)
    grid = np.arange(0, td[-1] + 1, STEP); yg = np.interp(grid, td, yd)
    gdays = [dates[0] + timedelta(days=float(g)) for g in grid]
    horizon_end = gdays[-1] + timedelta(days=int(math.ceil(88 / STEP) * STEP))
    rain, sm = weather((dates[0] - timedelta(days=31)).isoformat(), min(horizon_end, date(2026, 11, 13)).isoformat())
    full_days = [dates[0] + timedelta(days=k * STEP) for k in range(len(grid) + 16)]
    cov = covariates(full_days, rain, sm)
    if np.isnan(cov['sm'][:len(grid)]).any():
        raise SystemExit('soil moisture missing inside the series')

    from chronos import Chronos2Pipeline
    pipe = Chronos2Pipeline.from_pretrained('amazon/chronos-2', device_map='cpu')

    def predict(i, H, variant):
        steps = math.ceil(H / STEP)
        x = {'target': (yg[:i + 1] - yg[i]).astype(np.float32)}
        if variant != 'none':
            x['past_covariates'] = {k: v[:i + 1] for k, v in cov.items()}
        if variant == 'oracle':
            x['future_covariates'] = {k: v[i + 1:i + 1 + steps] for k, v in cov.items()}
        q, _ = pipe.predict_quantiles([x], prediction_length=steps, quantile_levels=Q)
        q = q[0][0].numpy()
        xs = np.r_[0, np.arange(1, steps + 1) * STEP]
        return [float(np.interp(H, xs, np.r_[0, q[:, k]])) for k in range(3)]

    report = dict(target='029A Zone 4 baseline, January to October 2026, 6-day steps',
                  covariates='ERA5 precipitation and ERA5-Land 0-7 cm soil moisture via the Open-Meteo archive API',
                  rule='past replaces none only if it lowers MAE at both 30 and 88 days', results={})
    for H in (30, 88):
        res = {}
        for variant in ('none', 'past', 'oracle'):
            e, c = [], []
            for i in range(10, len(grid)):
                if grid[i] + H > td[-1]:
                    break
                lo, m, hi = predict(i, H, variant)
                truth = float(np.interp(grid[i] + H, td, yd) - yg[i])
                e.append(abs(truth - m)); c.append(lo <= truth <= hi)
            res[variant] = dict(n=len(e), mae_mm=round(float(np.mean(e)), 3), interval80_coverage=round(float(np.mean(c)), 3))
        report['results'][f'{H}d'] = res
        print(H, 'days', {k: (v['mae_mm'], v['interval80_coverage']) for k, v in res.items()}, flush=True)
    r = report['results']
    report['adopt_past'] = bool(r['30d']['past']['mae_mm'] < r['30d']['none']['mae_mm'] and
                                r['88d']['past']['mae_mm'] < r['88d']['none']['mae_mm'])
    print('adopt past covariates:', report['adopt_past'])
    a.output.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
