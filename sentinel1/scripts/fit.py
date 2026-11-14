# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Fit Sentinel-1 HyP3 Burst InSAR products for Ocnele Mari.

Run with Python, GDAL, NumPy, pyproj and matplotlib installed:
    python fit.py ZIP_DIRECTORY OUTPUT_DIRECTORY

Any number of pairs and dates per track (the July to October 2026 run used 29 pairs and 16 dates per track; the
January to October extension uses more). Dates that no pair connects form separate groups: each group has its own
zero date and its own offset in the rate fit, so a gap never silently empties a zone. After a refit, run
`python scripts/pack_grids.py OUTPUT_DIRECTORY` so the committed grid chunks match the new summary.json.
"""
from pathlib import Path
import argparse
import json
import re
import zipfile

import numpy as np

ZONES = [(45.0892, 24.2872, 300), (45.0882, 24.2892, 250), (45.0930, 24.2565, 300), (45.0826, 24.2628, 250)]
FACTOR = -1000 * 0.05546576 / (4 * np.pi)  # LOS positive toward sensor; HyP3 phase positive away.
SUFFIXES = {'phase': 'unw_phase', 'coh': 'corr', 'comp': 'conncomp', 'water': 'water_mask', 'dem': 'dem',
            'theta': 'lv_theta', 'phi': 'lv_phi'}
STEP = 40


def geometry():
    """The 16.4 km analysis window around the town on a 40 m EPSG:32635 grid, the zone masks and reference bands."""
    from pyproj import Transformer
    project = Transformer.from_crs(4326, 32635, always_xy=True)
    cx, cy = project.transform(24.290, 45.088)
    bounds = (cx - 8200, cy - 8200, cx + 8200, cy + 8200)
    X, Y = np.meshgrid(bounds[0] + STEP * (.5 + np.arange(410)), bounds[3] - STEP * (.5 + np.arange(410)))
    distance = [np.hypot(X - x, Y - y) - r for lat, lon, r in ZONES for x, y in [project.transform(lon, lat)]]
    offset = np.min(distance, axis=0)
    return dict(project=project, cx=cx, cy=cy, bounds=bounds, X=X, Y=Y,
                masks=[d <= 0 for d in distance],
                refs=[(offset >= 3000) & (offset <= 6500),
                      (offset >= 3000) & (offset <= 6500) & (X < cx),
                      (offset >= 3000) & (offset <= 6500) & (X >= cx)],
                control=(offset >= 6500) & (offset <= 8000))


def read_product(p, bounds):
    from osgeo import gdal
    gdal.UseExceptions()
    with zipfile.ZipFile(p) as z:
        names = z.namelist()
    result = {}
    for key, suffix in SUFFIXES.items():
        name = next(n for n in names if n.endswith('_' + suffix + '.tif'))
        src = gdal.Open(f'/vsizip/{p.resolve()}/{name}')
        raster = gdal.Warp('', src, format='MEM', dstSRS='EPSG:32635', outputBounds=bounds,
                           xRes=STEP, yRes=STEP, resampleAlg='near', outputType=gdal.GDT_Float32, dstNodata=np.nan)
        result[key] = raster.ReadAsArray()
    return result


def date_groups(edges, n):
    """Label each date with its connected group in the pair design (0, 1, ...), ordered by first date."""
    label = list(range(n))
    def find(i):
        while label[i] != i:
            label[i] = label[label[i]]
            i = label[i]
        return i
    for i, j in edges:
        a, b = find(i), find(j)
        if a != b:
            label[max(a, b)] = min(a, b)
    roots = [find(i) for i in range(n)]
    order = {r: k for k, r in enumerate(sorted(set(roots)))}
    return np.array([order[r] for r in roots])


def solve(edges, n, data, weights, groups=None):
    """Per pixel and per date group, solve for one displacement per date with the group's first date fixed at zero.

    A pixel gets values for a group only if its retained pairs connect every date of that group; otherwise those dates
    stay NaN. With one group this is exactly the original single-network solver.
    """
    groups = date_groups(edges, n) if groups is None else groups
    shape = data.shape[1:]
    flat_w = weights.reshape(len(edges), -1)
    flat_d = data.reshape(len(edges), -1)
    estimated = np.full((n, flat_w.shape[1]), np.nan, np.float32)
    for g in np.unique(groups):
        dates = np.flatnonzero(groups == g)
        root = dates[0]
        rows = [k for k, (i, j) in enumerate(edges) if groups[i] == g and groups[j] == g]
        if not rows:
            continue
        known = np.zeros((n, flat_w.shape[1]), bool)
        known[root] = True
        for _ in range(len(dates)):
            old = known.sum()
            for k in rows:
                i, j = edges[k]
                valid = flat_w[k] > 0
                known[i] |= known[j] & valid
                known[j] |= known[i] & valid
            if known.sum() == old:
                break
        complete = np.flatnonzero(known[dates].all(axis=0))
        cols = [d for d in dates if d != root]
        A = np.zeros((len(rows), len(cols)))
        col = {d: c for c, d in enumerate(cols)}
        for r, k in enumerate(rows):
            i, j = edges[k]
            if i in col: A[r, col[i]] = -1
            if j in col: A[r, col[j]] = 1
        for ids in np.array_split(complete, max(1, (len(complete) + 3999) // 4000)):
            if not len(ids):
                continue
            w = flat_w[rows][:, ids].astype(float)
            y = np.nan_to_num(flat_d[rows][:, ids])
            normal = np.einsum('pi,pn,pj->nij', A, w, A, optimize=True)
            rhs = np.einsum('pi,pn->ni', A, w * y, optimize=True)
            estimated[root, ids] = 0
            estimated[np.ix_(cols, ids)] = np.linalg.solve(normal, rhs[..., None])[..., 0].T
    return estimated.reshape((n,) + shape)


def slopes(t, y, groups=None):
    """Least-squares slope through the dates with one offset per group (one group: the plain centred slope)."""
    groups = np.zeros(len(t), int) if groups is None else np.asarray(groups)
    tc = t.astype(float).copy()
    for g in np.unique(groups):
        m = groups == g
        tc[m] = t[m] - t[m].mean()
    return np.tensordot(tc / np.sum(tc ** 2), y, axes=1)


def stats(t, y, groups=None):
    groups = np.zeros(len(t), int) if groups is None else np.asarray(groups)
    fit = float(slopes(t, y, groups))
    dy = y[None, :] - y[:, None]
    i, j = np.triu_indices(len(t), 1)
    same = groups[i] == groups[j]                      # Theil-Sen never takes a slope across a gap
    sen = float(np.median(dy[i[same], j[same]] / (t[j[same]] - t[i[same]])))
    leave = [float(slopes(np.delete(t, k), np.delete(y, k), np.delete(groups, k))) for k in range(len(t))]
    span = float(sum(t[groups == g].max() - t[groups == g].min() for g in np.unique(groups)))
    return {'linear_mm_yr': fit, 'theil_sen_mm_yr': sen, 'window_fit_mm': fit * span,
            'date_fit_omission_range_mm_yr': [min(leave), max(leave)], 'displacement_mm': y.tolist(),
            'groups': groups.tolist()}


def fit_track(root, out, track, geo):
    files = sorted(root.glob(f'*-{track}-*.zip'))
    bad = [f.name for f in files if not zipfile.is_zipfile(f)]
    if not files or bad:
        raise SystemExit(f'{track}: {len(files)} product zips found, unreadable: {bad}')
    pairs = [re.findall(r'20\d{6}', f.stem) for f in files]
    dates = sorted(set(sum(pairs, [])))
    if len(dates) < 3:
        raise SystemExit(f'{track}: only {len(dates)} dates')
    ix = {d: i for i, d in enumerate(dates)}
    edges = [(ix[a], ix[b]) for a, b in pairs]
    groups = date_groups(edges, len(dates))
    print(track, f'{len(files)} pairs, {len(dates)} dates {dates[0]} to {dates[-1]}, {groups.max() + 1} date group(s)', flush=True)
    rows = [read_product(f, geo['bounds']) for f in files]
    dem = rows[0]['dem']
    t = (np.array([f'{d[:4]}-{d[4:6]}-{d[6:]}' for d in dates], dtype='datetime64[D]') -
         np.datetime64(f'{dates[0][:4]}-{dates[0][4:6]}-{dates[0][6:]}')).astype(float) / 365.25
    results = {}
    for label, min_coh, ref_idx, tropo in [('baseline', .35, 0, False), ('strict_coherence', .55, 0, False),
                                           ('west_reference', .35, 1, False), ('east_reference', .35, 2, False),
                                           ('elevation_correction', .35, 0, True)]:
        ds = []; ws = []
        for p in rows:
            valid = (p['coh'] >= min_coh) & (p['comp'] > 0) & (p['water'] == 1) & np.isfinite(p['phase'])
            reference = geo['refs'][ref_idx] & valid
            labels, counts = np.unique(p['comp'][reference], return_counts=True)
            assert len(labels), (track, label)
            valid &= p['comp'] == labels[np.argmax(counts)]
            reference = geo['refs'][ref_idx] & valid
            d = p['phase'] * FACTOR
            if tropo:
                ref = reference & np.isfinite(dem)
                b = np.polyfit(dem[ref], d[ref], 1)[0]
                d = d - b * (dem - np.median(dem[ref]))
            d = d - np.median(d[reference])
            ds.append(np.where(valid, d, np.nan))
            ws.append(np.where(valid, p['coh'] ** 2, 0))
        data = np.stack(ds); weights = np.stack(ws)
        y = solve(edges, len(dates), data, weights, groups)
        good = np.isfinite(y).all(axis=0)
        zone_results = {}
        for name, mask in zip(['zone_1', 'zone_2', 'zone_3', 'zone_4', 'outer_control'], geo['masks'] + [geo['control']]):
            keep = mask & good
            if keep.sum():
                zone_results[name] = {'pixels': int(keep.sum()), **stats(t, np.median(y[:, keep], axis=1), groups)}
            else:   # explicit, never a silent drop: the page shows "no data" with this reason
                zone_results[name] = {'pixels': 0, 'status': 'no pixel connected on every date'}
        if not any(v['pixels'] for v in zone_results.values()):
            raise SystemExit(f'{track} {label}: no zone and no control pixel has a complete series')
        results[label] = zone_results
        if label == 'baseline':
            fit = slopes(t, y, groups)
            errors = []
            index = {edge: i for i, edge in enumerate(edges)}
            for (i, k), ik in index.items():
                for j in range(i + 1, k):
                    if (i, j) in index and (j, k) in index:
                        errors.append(data[index[i, j]] + data[index[j, k]] - data[ik])
            c = np.asarray(errors)
            print(track, 'closure', len(c), np.nanmedian(abs(c)), np.nanpercentile(abs(c), 95), 'pixels', good.sum(), flush=True)
            theta = rows[0]['theta']; phi = rows[0]['phi']
            np.savez_compressed(out / (track + '.npz'), dates=np.array(dates), displacement_mm=y, rate_mm_yr=fit,
                                e=np.cos(theta) * np.cos(phi), u=np.sin(theta), bounds_utm=np.array(geo['bounds']),
                                groups=groups)
            plot(out, track, fit, geo)
            results['quality'] = {'closure_triangles': len(c), 'closure_abs_median_mm': float(np.nanmedian(abs(c))),
                                  'closure_abs_p95_mm': float(np.nanpercentile(abs(c), 95))}
        print(track, label, {k: (v['pixels'], round(v.get('linear_mm_yr', float('nan')), 2)) for k, v in zone_results.items()}, flush=True)
    return {'dates': dates, 'pair_count': len(files), 'date_groups': groups.tolist(), 'fits': results}


def plot(out, track, fit, geo):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    b, cx, cy = geo['bounds'], geo['cx'], geo['cy']
    fig, ax = plt.subplots(figsize=(7, 5), layout='constrained')
    im = ax.imshow(fit, extent=(b[0], b[2], b[1], b[3]), vmin=-35, vmax=35, cmap='RdBu')
    for lat, lon, r in ZONES:
        ax.add_patch(plt.Circle(geo['project'].transform(lon, lat), r, fill=False, color='#ecd638', lw=1.1))
    ax.set(xlim=(cx - 4500, cx + 3800), ylim=(cy - 3500, cy + 3500), title=f'Sentinel-1 {track} · LOS rate',
           xlabel='UTM easting (m)', ylabel='UTM northing (m)')
    fig.colorbar(im, ax=ax, label='mm/yr · positive toward satellite')
    fig.savefig(out / (track + '.png'), dpi=140)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('zip_directory', type=Path)
    ap.add_argument('output_directory', type=Path)
    ap.add_argument('--tracks', nargs='+', default=['029A', '007D'])
    a = ap.parse_args()
    a.output_directory.mkdir(parents=True, exist_ok=True)
    geo = geometry()
    summary = {track: fit_track(a.zip_directory, a.output_directory, track, geo) for track in a.tracks}
    (a.output_directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    main()
