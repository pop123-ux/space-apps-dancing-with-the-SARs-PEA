# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Backtest and export a Zone 4 LOS forecast from the summer 029A HyP3 archive.

    python forecast.py RAW_ZIP_DIR OUTPUT.json --as-of 2026-11-14 --end-date 2027-01-01 [--rain-csv CSV]

Models (all backtested on the same 30-day cutoffs, each re-inverted from interferograms that end by the cutoff):
  persistence, theil_sen, gaussian_process: fitted on the summer series up to the cutoff.
  long_term: a fixed line-of-sight rate from EGMS Ortho 2020-2025 (Up, East) projected onto Zone 4's own 029A look
      vector. It is set before any 2026 cutoff, so it carries no look-ahead.
Covariate test (not a UI model): 05's predeclared rain model (Theil-Sen, then ridge lambda=1 on standardised 7-day
rain, lag 0), from --rain-csv (notebooks/05/z4_screen_inputs.csv), refitted inside each cutoff.
Runs on CPU in seconds; no GDAL bindings needed (fit.read_product falls back to rasterio).
"""
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
MODELS = ('persistence', 'theil_sen', 'gaussian_process', 'long_term')
# EGMS Ortho 2020-2025, Zone 4 cell medians, mm/yr (05's cut, PR #9; sentinel1/docs/TEAM_HANDOFF.md)
EGMS_Z4 = dict(up=-3.1, east=4.9, cells=10, source='EGMS Ortho 2020-2025 L3, Zone 4 cell medians (05, PR #9)')
RAIN_LAMBDA = 1.0   # 05's predeclared ridge penalty; not tuned


def forecasts(t, y, ahead, long_term_rate=None):
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
    out = dict(persistence=np.zeros_like(a), theil_sen=drift, gaussian_process=drift + mean[1:] - mean[0])
    if long_term_rate is not None:
        out['long_term'] = long_term_rate * a / 365.25
    return out


def rain_model(t, y, x_train, x_now, x_future, ahead):
    """05's predeclared model: Theil-Sen trend, then ridge of the detrended LOS on standardised 7-day rain.
    Issuance assumes rain returns to its training mean; conditional uses the observed rain at the target date."""
    slope = float(theilslopes(y, t).slope)
    res = y - slope * t
    res = res - res.mean()
    mu, sd = x_train.mean(), x_train.std() or 1.0
    z = (x_train - mu) / sd
    beta = float(z @ res / (z @ z + RAIN_LAMBDA))
    a = np.asarray(ahead, float)
    issuance = slope * a + beta * (0.0 - (x_now - mu) / sd)
    conditional = slope * a + beta * ((np.asarray(x_future) - mu) / sd - (x_now - mu) / sd)
    return issuance, conditional, beta


def rain_by_date(path):
    import csv
    with open(path, newline='') as f:
        rows = [r for r in csv.DictReader(f) if r['track'] == '029A' and r['area'] == 'z4']
    return {date.fromisoformat(r['date']): float(r['rain7_mm']) for r in rows if r['rain7_mm']}


def observations(raw):
    geo = geometry()
    zone, ref = geo['masks'][3], geo['refs'][0]
    pairs, look = [], None
    for path in sorted(raw.glob('*-029A-*.zip')):
        a,b = [date.fromisoformat(s) for s in re.findall(r'20\d{6}',path.stem)]
        if not START <= a < b <= END:
            continue
        p = read_product(path, geo['bounds'])
        if look is None:   # Zone 4 look vector, target to sensor, as in fit.py
            look = (float(np.nanmedian((np.cos(p['theta']) * np.cos(p['phi']))[zone])),
                    float(np.nanmedian(np.sin(p['theta'])[zone])))
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
    return pairs, look


def invert(pairs, dates):
    ix = {d:i for i,d in enumerate(dates)}
    rows = [(ix[a],ix[b],d,w) for a,b,d,w in pairs if a in ix and b in ix]
    if not rows:
        raise ValueError('No pairs for reconstruction')
    return solve([(i,j) for i,j,*_ in rows],len(dates),
                 np.stack([d for _,_,d,_ in rows]),np.stack([w for _,_,_,w in rows]),
                 np.zeros(len(dates), dtype=int))


def build(raw, as_of, end_date=None, rain_csv=None):
    pairs, (e, u) = observations(raw)
    lt_rate = e * EGMS_Z4['east'] + u * EGMS_Z4['up']   # north ignored (EGMS Ortho has none)
    rain = rain_by_date(rain_csv) if rain_csv else None
    rain_scores = {'issuance': [], 'conditional': []}
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
        preds = forecasts(t,y,ahead,lt_rate)
        extra = {}
        if rain is not None and all(d in rain for d in train_dates + test_dates):
            xt = np.array([rain[d] for d in train_dates])
            iss, cond, beta = rain_model(t, y - y[-1], xt, xt[-1], [rain[d] for d in test_dates], ahead)
            rain_scores['issuance'].append(abs(truth[-1] - float(iss[-1])))
            rain_scores['conditional'].append(abs(truth[-1] - float(cond[-1])))
            extra = dict(rain7_beta_mm_per_sd=beta, rain7_issuance_mm=iss.tolist(), rain7_conditional_mm=cond.tolist())
        folds.append(dict(origin=origin.isoformat(), lead_days=ahead, **extra,
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
    pred = forecasts(t,hist,ahead,lt_rate)
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
                metrics=metrics, folds=folds,
                long_term=dict(rate_los_mm_yr=lt_rate, egms_up_mm_yr=EGMS_Z4['up'], egms_east_mm_yr=EGMS_Z4['east'],
                               egms_cells=EGMS_Z4['cells'], look_e=e, look_u=u, source=EGMS_Z4['source'],
                               note='Projected onto 029A line of sight with Zone 4 median look vector; north ignored. '
                                    'Fixed before every 2026 cutoff, so no look-ahead. Cross-check: the Jan-Oct 2026 '
                                    'Sentinel-1 fit gives about -5.4 mm/yr (not yet in the repository).'),
                covariate_tests=None if rain is None else dict(
                    rain7=dict(source='ERA5 daily via Open-Meteo, 7-day sums at 45.088 N, 24.290 E (05, PR #9)',
                               model='Theil-Sen then ridge (lambda=1) on standardised 7-day rain, lag 0; predeclared by 05',
                               folds=len(rain_scores['issuance']),
                               mae_mm={k: float(np.mean(v)) for k, v in rain_scores.items() if v},
                               note='Refitted on a re-inversion at each cutoff (removes the look-ahead in 05\'s first '
                                    'run). Conditional uses observed future rain, so it is a scenario, not a forecast.')))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--as-of',type=date.fromisoformat,required=True)
    parser.add_argument('--end-date',type=date.fromisoformat)
    parser.add_argument('--rain-csv',type=Path,help='notebooks/05/z4_screen_inputs.csv (05)')
    args=parser.parse_args()
    args.output.write_text(json.dumps(build(args.raw,args.as_of,args.end_date,args.rain_csv),indent=2,allow_nan=False)+'\n')
