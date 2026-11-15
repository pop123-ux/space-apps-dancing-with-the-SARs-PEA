# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Compare a refit with a committed fit: every zone number of every run, and the baseline grids.

    python scripts/check_reproduction.py COMMITTED_DIR REFIT_DIR -o report.json

Both directories hold summary.json and <track>.npz (restore committed grids first with scripts/restore_grids.py).
Reports the largest absolute difference per quantity. Used to show that the January to November refit reads the same
products the same way as the committed January to October fit, before the new dates are trusted.
"""
from pathlib import Path
import argparse
import json

import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('committed', type=Path)
    ap.add_argument('refit', type=Path)
    ap.add_argument('-o', '--output', type=Path, required=True)
    a = ap.parse_args()
    old = json.loads((a.committed / 'summary.json').read_text())
    new = json.loads((a.refit / 'summary.json').read_text())
    report = {}
    for track in old:
        r = report[track] = dict(dates_equal=old[track]['dates'] == new[track]['dates'],
                                 pairs=[old[track]['pair_count'], new[track]['pair_count']], zones={})
        worst = 0.0
        for run, zones in old[track]['fits'].items():
            if run == 'quality':
                r['closure_p95_mm'] = [zones['closure_abs_p95_mm'], new[track]['fits']['quality']['closure_abs_p95_mm']]
                continue
            for zone, v in zones.items():
                w = new[track]['fits'].get(run, {}).get(zone, {})
                if v.get('pixels', 0) != w.get('pixels', 0):
                    r['zones'][f'{run}/{zone}'] = dict(pixels=[v.get('pixels', 0), w.get('pixels', 0)])
                    worst = float('inf')
                    continue
                if 'displacement_mm' in v:
                    d = float(np.max(np.abs(np.subtract(v['displacement_mm'], w['displacement_mm']))))
                    d = max(d, abs(v['linear_mm_yr'] - w['linear_mm_yr']), abs(v['window_fit_mm'] - w['window_fit_mm']))
                    worst = max(worst, d)
        r['max_abs_zone_difference'] = worst
        go, gn = a.committed / f'{track}.npz', a.refit / f'{track}.npz'
        if go.exists() and gn.exists():
            o, n = np.load(go), np.load(gn)
            same = np.isfinite(o['displacement_mm']) == np.isfinite(n['displacement_mm'])
            both = np.isfinite(o['displacement_mm']) & np.isfinite(n['displacement_mm'])
            r['grid'] = dict(finite_pattern_equal=bool(same.all()),
                             max_abs_displacement_mm=float(np.max(np.abs(o['displacement_mm'][both] - n['displacement_mm'][both]))) if both.any() else None)
        print(track, json.dumps(r))
    a.output.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
