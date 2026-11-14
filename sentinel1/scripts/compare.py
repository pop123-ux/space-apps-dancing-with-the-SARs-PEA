# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Summarize matched-pixel Sentinel-1 rates and an exploratory up/east split for the common date window.

    python compare.py ANALYSIS_DIRECTORY [--window 2026-07-07 2026-10-04]

The window defaults to common.COMMON_WINDOW (the dates both radars cover). Only real acquisition dates inside it are
used, and the rate is the same estimator as fit.py: a least-squares line through the dates (one offset per date
group), not a refit of a daily-interpolated series. North motion is assumed zero; the result is diagnostic.
"""
from pathlib import Path
import argparse
import json
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # the repo root, for common.py
import common as C                                              # noqa: E402
from fit import ZONES, slopes                                   # noqa: E402


def window_rates(stack, start, end):
    """Per-pixel LOS rate (mm/yr) through the real dates inside [start, end]; NaN unless every one of them is finite."""
    d = np.array([f'{s[:4]}-{s[4:6]}-{s[6:]}' for s in stack['dates']], dtype='datetime64[D]')
    keep = (d >= np.datetime64(start)) & (d <= np.datetime64(end))
    groups = stack['groups'][keep] if 'groups' in stack.files else np.zeros(keep.sum(), int)
    t = (d[keep] - d[keep][0]).astype(float) / 365.25
    y = stack['displacement_mm'][keep]
    good = np.isfinite(y).all(axis=0)
    rate = np.full(good.shape, np.nan)
    rate[good] = slopes(t, y[:, good], groups)
    return rate, [str(x) for x in d[keep]]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('analysis_directory', type=Path)
    ap.add_argument('--window', nargs=2, default=list(C.COMMON_WINDOW), metavar=('START', 'END'))
    a = ap.parse_args()
    from pyproj import Transformer
    root = a.analysis_directory
    asc, desc = [np.load(root / (tr + '.npz')) for tr in ('029A', '007D')]
    project = Transformer.from_crs(4326, 32635, always_xy=True)
    xmin, ymin, xmax, ymax = asc['bounds_utm']
    X, Y = np.meshgrid(np.arange(xmin + 20, xmax, 40), np.arange(ymax - 20, ymin, -40))
    av, a_dates = window_rates(asc, *a.window)
    dv, d_dates = window_rates(desc, *a.window)
    ea, ua, ed, ud = asc['e'], asc['u'], desc['e'], desc['u']
    det = ea * ud - ed * ua
    with np.errstate(invalid='ignore', divide='ignore'):
        up = (ea * dv - ed * av) / det
        east = (ud * av - ua * dv) / det
    valid = np.isfinite(up) & np.isfinite(east) & (np.abs(det) > .2)
    dist = [np.hypot(X - x, Y - y) - r for lat, lon, r in ZONES for x, y in [project.transform(lon, lat)]]
    offset = np.minimum.reduce(dist)
    regions = {f'zone_{i}': m <= 0 for i, m in enumerate(dist, 1)}
    regions['outer_control'] = (offset >= 6500) & (offset <= 8000)
    summary = {'window': a.window, 'dates_029A': a_dates, 'dates_007D': d_dates,
               'method': 'least-squares line through the real dates in the window; north assumed zero; diagnostic'}
    for name, m in regions.items():
        k = m & valid
        summary[name] = {'matched_pixels': int(k.sum())}
        if k.any():
            summary[name].update({key: float(np.median(val[k])) for key, val in
                                  [('asc_mm_yr', av), ('desc_mm_yr', dv), ('up_mm_yr', up), ('east_mm_yr', east)]})
    print(json.dumps(summary, indent=2))
    (root / 'matched_geometry_exploratory.json').write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    main()
