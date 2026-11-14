# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Add a zero-shot Chronos-2 path, with an 80 % interval, to the Zone 4 forecast export.

    python forecast_chronos.py ../../products/ocnele_mari/forecast.json [--janoct ../analysis_jan_oct/summary.json]

Run after forecast.py, in an environment with `chronos-forecasting>=2` and CPU torch (about 1.4 GB; not needed by the
page or the rest of the pipeline). Model: amazon/chronos-2 from Hugging Face, used zero-shot (no fine-tuning) on CPU.

Writes into forecast.json, leaving every existing path, metric and the default `model` unchanged:
  model_paths_mm.chronos2       median path on the export's dates (same reference as the other paths)
  intervals.chronos2            q10 and q90 paths (80 % interval)
  metrics.chronos2              30-day MAE on forecast.py's own cutoffs (their training series are in folds[].train_mm)
  chronos2                      model id, package version, quantile coverage, and a 30- and 88-day backtest on the
                                January to October 029A Zone 4 series (final reconstruction cut at each cutoff, so a
                                small look-ahead remains; cutoffs overlap, so the folds are not independent).
"""
import argparse
import json
import math
from datetime import date, timedelta
from pathlib import Path

import numpy as np

Q = [0.1, 0.5, 0.9]
STEP = 6.0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('forecast', type=Path)
    ap.add_argument('--janoct', type=Path, help='sentinel1/analysis_jan_oct/summary.json for the longer backtest')
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
    a.forecast.write_text(json.dumps(f, indent=2, allow_nan=False) + '\n')
    print({k: round(v['mae_mm'], 2) for k, v in f['metrics'].items()}, '| 1 Jan', round(f['model_paths_mm']['chronos2'][-1], 2),
          '80%', [round(f['intervals']['chronos2'][k][-1], 2) for k in ('q10', 'q90')])
    print({k: (v if not isinstance(v, dict) else {kk: (round(vv, 2) if isinstance(vv, float) else vv) for kk, vv in v.items()}) for k, v in block.items() if k != 'note'})


if __name__ == '__main__':
    main()
