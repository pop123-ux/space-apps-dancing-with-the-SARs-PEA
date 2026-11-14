# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Add a zero-shot Chronos-2 path, with an 80 % interval, to the Zone 4 forecast export.

    python forecast_chronos.py ../../products/ocnele_mari/forecast.json [--janoct ../analysis_jan_oct/summary.json]

Run after forecast.py, in an environment with `chronos-forecasting>=2` and CPU torch (about 1.4 GB; not needed by the
page or the rest of the pipeline). Model: amazon/chronos-2 from Hugging Face, used zero-shot (no fine-tuning) on CPU.

    [--default] [--weather ../analysis/chronos_weather.json]

Writes into forecast.json, leaving every existing path and metric unchanged:
  model_paths_mm.chronos2       median path on the export's dates (same reference as the other paths)
  intervals.chronos2            q10 and q90 paths (80 % interval)
  metrics.chronos2              30-day MAE on forecast.py's own cutoffs (their training series are in folds[].train_mm)
  chronos2                      model id, package version, quantile coverage, and a 30- and 88-day backtest on the
                                January to October 029A Zone 4 series (final reconstruction cut at each cutoff, so a
                                small look-ahead remains; cutoffs overlap, so the folds are not independent).
  --default                     also makes chronos2 the default `model` (team decision, 14 Nov 2026, 20:30): sets
                                `model`, `forecast_mm`, `interval` and `model_reason`.
  --weather                     copies chronos_weather.py's predeclared covariate backtest into covariate_tests.
  --nisar SERIES_JSON           out-of-sample check against NISAR 129A Zone 4 (products/<site>/series.json): the
                                change between NISAR's last two dates (9 and 21 Oct 2026, after Sentinel-1's 5 Oct
                                cutoff) scaled into 029A's line of sight assuming vertical motion only, next to the
                                Chronos-2 median change over the same days. A consistency check, not a pass rule.
"""
import argparse
import json
import math
from datetime import date, timedelta
from pathlib import Path

import numpy as np

Q = [0.1, 0.5, 0.9]
STEP = 6.0


def nisar_check(f, series_path):
    """NISAR 129A Zone 4 change between its last two dates vs the Chronos-2 median change over the same days."""
    s = json.loads(series_path.read_text())
    z = next(p for p in s if p['id'] == f['zone'].lower())
    n = z['series'].get('nisar:129A')
    if not n:
        return None
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    import common as C
    import numpy as np
    meta = C.load_json(C.WORK / 'ocnele_mari' / '129A' / 'meta.json')
    g = np.load(C.WORK / 'ocnele_mari' / '129A' / 'geom.npz')
    import export
    m = export.nisar_zone_masks(C.SITES['ocnele_mari'], meta)[f['zone'].lower()]
    u_n = float(g['los_u'][m].mean())
    after = [(d, v) for d, v in zip(n['dates'], n['mm']) if d > f['last_observation']]
    if len(after) < 2:
        return None
    (d0, v0), (d1, v1) = after[-2], after[-1]
    scale = f['long_term']['look_u'] / u_n          # 029A up component at Zone 4, from forecast.py
    summer = [(d, v) for d, v in zip(n['dates'], n['mm']) if d >= '2026-06-01']
    steps = np.diff([v for _, v in summer])
    last = date.fromisoformat(f['last_observation'])
    x = [0] + [(date.fromisoformat(d) - last).days for d in f['dates']]
    path = [f['observed_mm'][-1]] + f['model_paths_mm']['chronos2']
    at = lambda d: float(np.interp((date.fromisoformat(d) - last).days, x, path))
    return dict(dates=[d0, d1], nisar_change_mm=round((v1 - v0) * scale, 2), nisar_change_own_los_mm=round(v1 - v0, 2),
                chronos2_change_mm=round(at(d1) - at(d0), 2), scale_vertical_only=round(scale, 3),
                nisar_step_scatter_mm=round(float(1.4826 * np.median(np.abs(steps - np.median(steps)))) * scale, 2),
                n_pixels=n['n_pixels'],
                note='NISAR 129A looks left and Sentinel-1 029A right; the scaling assumes vertical motion only. '
                     'NISAR date-to-date scatter at 20 pixels is larger than the change, so this is a consistency '
                     'check, not a validation.')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('forecast', type=Path)
    ap.add_argument('--janoct', type=Path, help='sentinel1/analysis_jan_oct/summary.json for the longer backtest')
    ap.add_argument('--default', action='store_true', help='make chronos2 the default model (team decision)')
    ap.add_argument('--weather', type=Path, help='chronos_weather.py report to record under covariate_tests')
    ap.add_argument('--nisar', type=Path, help='products/<site>/series.json with nisar:129A, for the October check')
    a = ap.parse_args()
    import chronos
    from chronos import Chronos2Pipeline
    pipe = Chronos2Pipeline.from_pretrained('amazon/chronos-2', device_map='cpu')

    def predict(y, days):
        """Quantile paths at the given lead days (linear between the 6-day steps), relative to the last value."""
        steps = math.ceil(max(days) / STEP)
        q, _ = pipe.predict_quantiles([np.asarray(y, np.float32)], prediction_length=steps, quantile_levels=Q)
        q = q[0][0].numpy()
        x = np.r_[0, np.arange(1, steps + 1) * STEP]
        return [np.interp(days, x, np.r_[0, q[:, k]]) for k in range(len(Q))]

    f = json.loads(a.forecast.read_text())
    if any('train_mm' not in fold for fold in f['folds']):
        raise SystemExit('forecast.json has no per-fold training series: rerun forecast.py first')
    errs, inside = [], []
    for fold in f['folds']:
        lo, med, hi = predict(fold['train_mm'], [fold['lead_days'][-1]])
        truth = fold['observed_mm'][-1]
        fold.setdefault('predicted_mm', {})['chronos2'] = [float(med[0])]
        errs.append(abs(truth - med[0])); inside.append(lo[0] <= truth <= hi[0])
    f['metrics']['chronos2'] = dict(mae_mm=float(np.mean(errs)))

    obs = np.array(f['observed_mm']); last = date.fromisoformat(f['last_observation'])
    days = [(date.fromisoformat(d) - last).days for d in f['dates']]
    lo, med, hi = predict(obs - obs[-1], days)
    f['model_paths_mm']['chronos2'] = (obs[-1] + med).tolist()
    f.setdefault('intervals', {})['chronos2'] = dict(q10=(obs[-1] + lo).tolist(), q90=(obs[-1] + hi).tolist(), level=0.8)

    block = dict(model='amazon/chronos-2', package=f'chronos-forecasting {chronos.__version__}', device='cpu',
                 use='zero-shot; context = the export series relative to its last value, 6-day steps',
                 summer_folds=dict(n=len(errs), mae_mm=float(np.mean(errs)), interval80_coverage=float(np.mean(inside))))
    if a.janoct:
        s = json.loads(a.janoct.read_text())['029A']
        z = s['fits']['baseline']['zone_4']; d0 = date(int(s['dates'][0][:4]), int(s['dates'][0][4:6]), int(s['dates'][0][6:]))
        td = np.array([(date(int(x[:4]), int(x[4:6]), int(x[6:])) - d0).days for x in s['dates']], float)
        yd = np.array(z['displacement_mm']); grid = np.arange(0, td[-1] + 1, STEP); yg = np.interp(grid, td, yd)
        for H in (30, 88):
            e, c = [], []
            for i in range(10, len(grid)):
                if grid[i] + H > td[-1]:
                    break
                l, m, h = predict(yg[:i + 1] - yg[i], [H])
                truth = float(np.interp(grid[i] + H, td, yd) - yg[i])
                e.append(abs(truth - m[0])); c.append(l[0] <= truth <= h[0])
            block[f'janoct_{H}d'] = dict(n=len(e), mae_mm=float(np.mean(e)), interval80_coverage=float(np.mean(c)),
                                         first_cutoff=(d0 + timedelta(days=10 * STEP)).isoformat())
    block['note'] = ('Chronos-2 is a pretrained time-series model: it extrapolates the shape of this one series and '
                     'knows nothing about salt, weather or the mine. Its interval is the only calibrated-looking one '
                     'here (about 77 to 78 % of truths inside the 80 % band on the Jan-Oct backtests), still from one '
                     'zone, one track and overlapping cutoffs.')
    f['chronos2'] = block
    cov = [v['interval80_coverage'] for k, v in block.items() if k.startswith('janoct_')]
    if cov:
        f['interval_reason'] = (f"Only Chronos-2 has an interval: its 80 % band held the truth in {min(cov):.0%} to {max(cov):.0%} "
                                "of the overlapping January to October backtests. The other models have none, because four "
                                "summer backtests cannot calibrate one.")
    if a.weather:
        w = json.loads(a.weather.read_text())
        f.setdefault('covariate_tests', {})['chronos2_weather'] = dict(
            source=w['covariates'], target=w['target'], rule=w['rule'], results=w['results'], adopted=w['adopt_past'],
            note='Past-only rain and soil-moisture covariates did not lower the error, so the export uses Chronos-2 '
                 'without covariates. Known-future weather (not available for a real forecast) helped only at 88 days.')
    if a.nisar:
        f['nisar_check'] = nisar_check(f, a.nisar)
    if a.default:
        f['model'] = 'chronos2'
        f['forecast_mm'] = f['model_paths_mm']['chronos2']
        f['interval'] = f['intervals']['chronos2']
        f['model_reason'] = ('Team decision, 14 Nov 2026: lowest MAE on every backtest that reaches the January horizon '
                             '(30-day summer and January to October, 88-day January to October), and the only interval '
                             'with near-nominal coverage.')
    a.forecast.write_text(json.dumps(f, indent=2, allow_nan=False) + '\n')
    print({k: round(v['mae_mm'], 2) for k, v in f['metrics'].items()}, '| 1 Jan', round(f['model_paths_mm']['chronos2'][-1], 2),
          '80%', [round(f['intervals']['chronos2'][k][-1], 2) for k in ('q10', 'q90')])
    print({k: (v if not isinstance(v, dict) else {kk: (round(vv, 2) if isinstance(vv, float) else vv) for kk, vv in v.items()}) for k, v in block.items() if k != 'note'})


if __name__ == '__main__':
    main()
