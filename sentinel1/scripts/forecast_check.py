# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Score an issued Zone 4 forecast against Sentinel-1 acquisitions made after it was issued.

    python forecast_check.py RAW_ZIP_DIR FORECAST_JSON --last-date 2026-11-10 -o check.json

The forecast in FORECAST_JSON was issued from 029A data up to its `last_observation` (5 Oct 2026). This re-inverts the
same summer pair design (each date with the one and two before it, baseline run, as in forecast.py) from 7 Jul to
--last-date, keeps the Zone 4 pixels connected on every date, and compares the measured change since the last
observation with every model path and with the Chronos-2 80 % interval, date by date.

Nothing is tuned: the forecast file is read as published. The measured values come from a longer inversion than the
one the forecast was trained on, so the pixel set can differ (both counts are reported). Six dates are one test of one
forecast, not a skill score.
"""
from datetime import date, timedelta
from pathlib import Path
import argparse
import json

import numpy as np

import forecast as F


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('raw', type=Path)
    ap.add_argument('forecast', type=Path)
    ap.add_argument('--last-date', type=date.fromisoformat, required=True)
    ap.add_argument('-o', '--output', type=Path, required=True)
    a = ap.parse_args()
    f = json.loads(a.forecast.read_text())
    issued = date.fromisoformat(f['last_observation'])
    F.END = a.last_date
    pairs, _ = F.observations(a.raw)
    dates = sorted({d for p, q, *_ in pairs for d in (p, q)})
    y = F.invert(pairs, dates)
    keep = np.isfinite(y).all(axis=0)
    if keep.sum() < F.MIN_PIXELS:
        raise SystemExit(f'only {keep.sum()} Zone 4 pixels connected from {dates[0]} to {dates[-1]}')
    series = np.median(y[:, keep], axis=1)
    i0 = dates.index(issued)
    later = dates[i0 + 1:]
    measured = {d: float(series[dates.index(d)] - series[i0]) for d in later}
    x = [0] + [(date.fromisoformat(d) - issued).days for d in f['dates']]
    def path_at(values, d):
        return float(np.interp((d - issued).days, x, [f['observed_mm'][-1]] + list(values)) - f['observed_mm'][-1])
    rows = []
    for d in later:
        r = dict(date=d.isoformat(), days_after=(d - issued).days, measured_change_mm=round(measured[d], 2),
                 predicted_change_mm={k: round(path_at(v, d), 2) for k, v in f['model_paths_mm'].items()})
        iv = (f.get('intervals') or {}).get('chronos2')
        if iv:
            lo, hi = path_at(iv['q10'], d), path_at(iv['q90'], d)
            r['chronos2_interval_mm'] = [round(lo, 2), round(hi, 2)]
            r['inside_chronos2_interval'] = bool(lo <= measured[d] <= hi)
        rows.append(r)
    mae = {k: round(float(np.mean([abs(r['measured_change_mm'] - r['predicted_change_mm'][k]) for r in rows])), 2)
           for k in f['model_paths_mm']}
    inside = [r['inside_chronos2_interval'] for r in rows if 'inside_chronos2_interval' in r]
    out = dict(forecast_issued_from=issued.isoformat(), forecast_model=f.get('model'), checked_through=later[-1].isoformat(),
               new_dates=len(later), zone=f['zone'], track=f['track'], scenario='baseline',
               pixels_connected=int(keep.sum()), pixels_in_forecast=f.get('connected_pixels'),
               pairs=len(pairs), rows=rows, mae_mm=mae,
               chronos2_inside_80pct=f'{sum(inside)} of {len(inside)}' if inside else None,
               note='Measured change since the forecast was issued, from a 7 Jul to '
                    f'{later[-1].isoformat()} re-inversion of the 029A summer pair design (baseline run). One forecast '
                    f'checked on {len(later)} later dates; the dates share one reference, so they are not independent.')
    a.output.write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps({k: out[k] for k in ('checked_through', 'pixels_connected', 'mae_mm', 'chronos2_inside_80pct')}))


if __name__ == '__main__':
    main()
