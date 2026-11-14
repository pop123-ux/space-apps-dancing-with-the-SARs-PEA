# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Backtest and export a Zone 4 LOS forecast from the summer 029A HyP3 archive."""
import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import re

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.stats import theilslopes

from fit import FACTOR, geometry, read_product, solve

START, END = date(2026, 7, 7), date(2026, 10, 5)
HORIZON = 30
MIN_HISTORY, MIN_PIXELS = 8, 10
MODELS = ('persistence', 'theil_sen', 'gaussian_process')


def forecasts(t, y, ahead):
    """Forecast relative to the last available epoch. GP residuals have a Matérn 3/2 kernel."""
    slope = float(theilslopes(y, t).slope)
    a = np.asarray(ahead, float)
    drift = slope * a
    residual = y - slope * t
    residual = residual - np.median(residual)
    def kernel(x, z, length, signal):
        d = np.sqrt(3) * np.abs(x[:, None] - z[None, :]) / length
        return signal**2 * (1 + d) * np.exp(-d)
    best = None
    scale = max(float(np.std(residual)), .25)
    for length in (6., 12., 24.):
        for signal in (scale * .5, scale):
            for noise in (scale * .25, scale * .5, scale):
                cov = kernel(t, t, length, signal) + np.eye(t.size) * (noise**2 + 1e-9)
                ch = cho_factor(cov)
                alpha = cho_solve(ch, residual)
                loss = .5 * (residual @ alpha) + np.log(np.diag(ch[0])).sum()
                if best is None or loss < best[0]:
                    best = (loss, length, signal, alpha)
    _, length, signal, alpha = best
    mean = kernel(np.r_[0., a], t, length, signal) @ alpha
    return dict(persistence=np.zeros_like(a), theil_sen=drift, gaussian_process=drift + mean[1:] - mean[0])


def observations(raw):
    geo = geometry()
    zone, ref = geo['masks'][3], geo['refs'][0]
    pairs = []
    for path in sorted(raw.glob('*-029A-*.zip')):
        a,b = [date.fromisoformat(s) for s in re.findall(r'20\d{6}',path.stem)]
        if not START <= a < b <= END:
            continue
        p = read_product(path, geo['bounds'])
        valid = (p['coh'] >= .35) & (p['comp'] > 0) & (p['water'] == 1) & np.isfinite(p['phase'])
        labels, counts = np.unique(p['comp'][ref & valid], return_counts=True)
        if not len(labels):
            raise ValueError(f'{path.name}: no valid reference')
        valid &= p['comp'] == labels[np.argmax(counts)]
        d = p['phase'] * FACTOR
        d -= np.median(d[ref & valid])
        pairs.append((a,b,np.where(valid[zone],d[zone],np.nan),
                      np.where(valid[zone],p['coh'][zone]**2,0.)))
    if len(pairs)!=29 or len({(a,b) for a,b,*_ in pairs})!=29:
        raise ValueError('Expected the 29 unique summer 029A pairs')
    return pairs


def invert(pairs, dates):
    ix = {d:i for i,d in enumerate(dates)}
    rows = [(ix[a],ix[b],d,w) for a,b,d,w in pairs if a in ix and b in ix]
    if not rows:
        raise ValueError('No pairs for reconstruction')
    return solve([(i,j) for i,j,*_ in rows],len(dates),
                 np.stack([d for _,_,d,_ in rows]),np.stack([w for _,_,_,w in rows]),
                 np.zeros(len(dates), dtype=int))


def build(raw, as_of, end_date=None):
    pairs = observations(raw)
    dates = sorted({d for a,b,*_ in pairs for d in (a,b)})
    folds = []
    for n in range(MIN_HISTORY,len(dates)):
        train_dates = dates[:n]
        origin = train_dates[-1]
        if origin + timedelta(days=HORIZON) not in dates[n:]:
            continue
        test_dates = [d for d in dates[n:] if (d-origin).days <= HORIZON]
        # Training edges end at the cutoff. Validation edges start at or after it.
        hist = invert(pairs,train_dates)
        target = invert(pairs,[origin,*test_dates])
        train_pixels = np.isfinite(hist).all(axis=0)
        score_pixels = train_pixels & np.isfinite(target).all(axis=0)
        if min(train_pixels.sum(),score_pixels.sum()) < MIN_PIXELS:
            continue
        t = np.array([(d-origin).days for d in train_dates])
        ahead = [(d-origin).days for d in test_dates]
        y = np.median(hist[:,train_pixels],axis=1)
        truth = np.median(target[1:,score_pixels],axis=1)
        preds = forecasts(t,y,ahead)
        folds.append(dict(origin=origin.isoformat(), lead_days=ahead,
                          training_pixels=int(train_pixels.sum()), scoring_pixels=int(score_pixels.sum()),
                          observed_mm=truth.tolist(), predicted_mm={k:v.tolist() for k,v in preds.items()}))
    if not folds:
        raise ValueError('No eligible 30-day backtest folds')
    metrics = {k:dict(mae_mm=float(np.mean([abs(f['observed_mm'][-1]-f['predicted_mm'][k][-1]) for f in folds])))
               for k in MODELS}
    candidate = min(MODELS,key=lambda k:metrics[k]['mae_mm'])
    final = invert(pairs,dates)
    keep = np.isfinite(final).all(axis=0)
    if keep.sum()<MIN_PIXELS:
        raise ValueError('Too few connected pixels in the final reconstruction')
    last = dates[-1]
    t = np.array([(d-last).days for d in dates])
    hist = np.median(final[:,keep],axis=1)
    end = end_date or last + timedelta(days=HORIZON)
    horizon = (end - last).days
    if horizon <= 0:
        raise ValueError('Forecast end date must follow the last acquisition')
    ahead = np.array([*range(6, horizon, 6), horizon])
    pred = forecasts(t,hist,ahead)
    return dict(zone='z4', track='029A', sensor='s1', window='jul_oct', scenario='baseline',
                last_observation=last.isoformat(), end_date=end.isoformat(), as_of=as_of.isoformat(),
                status='retrospective' if end<=as_of else 'experimental',
                horizon_days=horizon, backtest_horizon_days=HORIZON, connected_pixels=int(keep.sum()), model=candidate,
                training_dates=[d.isoformat() for d in dates], observed_mm=hist.tolist(),
                dates=[(last+timedelta(days=int(h))).isoformat() for h in ahead],
                forecast_mm=(hist[-1]+pred[candidate]).tolist(),
                model_paths_mm={key:(hist[-1]+value).tolist() for key,value in pred.items()}, interval=None,
                interval_reason='The backtests give too little evidence to calibrate a prediction interval.',
                selection_metric='Mean absolute error at 30 days relative to the cutoff',
                metrics=metrics, folds=folds)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--as-of',type=date.fromisoformat,required=True)
    parser.add_argument('--end-date',type=date.fromisoformat)
    args=parser.parse_args()
    args.output.write_text(json.dumps(build(args.raw,args.as_of,args.end_date),indent=2,allow_nan=False)+'\n')
