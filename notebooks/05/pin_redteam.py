# Owner: 05 · Validator (Paul)
"""Red-team the page's pin ("Can you build here?").

Ports buildCheck, lineForecast, pinPoint and surroundings from app/main.js and runs them on
random spots across the published point files. Three questions:
  A. On ground outside every zone (+500 m), how often does the pin say "Not recommended"?
     (false-alarm rate; most of this ground should be stable)
  B. How often does it say "No warning sign" while the spot's own trend is within 2 sigma of zero?
     (a green tick on noise)
  C. Is the trend's sigma honest? Compare the stated sigma (dates assumed independent) with the
     spread of slopes between neighbouring stable spots 300 m apart.
Run from the repo root: python notebooks/05/pin_redteam.py
"""
import json, math, random, sys
import numpy as np

SITE = 'products/ocnele_mari'
PIN_R, RING, DIFF_MIN, SINK = 120, 300, 5, -15
END = np.datetime64('2029-01-01')

def zones():
    s = json.load(open(f'{SITE}/series.json', encoding='utf-8'))
    out = []
    def walk(o):
        if isinstance(o, dict):
            if {'lon', 'lat', 'r_m'} <= o.keys(): out.append((o.get('id'), o['lon'], o['lat'], o['r_m']))
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(s)
    return list({z[0]: z for z in out}.values())

def load(path):
    d = json.load(open(path, encoding='utf-8'))
    lon, lat = np.array(d['lon'], float), np.array(d['lat'], float)
    ch = np.array([[np.nan if v is None else v * d['scale'] for v in col] for col in d['change']])  # dates x points
    return d['dates'], lon, lat, ch

def metres(lon, lat, at):
    return np.hypot((lon - at[0]) * 111320 * math.cos(math.radians(at[1])), (lat - at[1]) * 110540)

def pin_series(P, at):
    dates, lon, lat, ch = P
    m = metres(lon, lat, at) <= PIN_R
    if not m.any(): return None
    with np.errstate(all='ignore'):
        y = np.nanmedian(ch[:, m], axis=1)
    ok = np.isfinite(y)
    t = np.array(dates, dtype='datetime64[D]')[ok]
    return t, y[ok], int(m.sum())

def line(t, y):
    n = len(y)
    if n < 4: return None
    x = (t - t[0]).astype(float) / 365.25
    xm, ym = x.mean(), y.mean(); sxx = ((x - xm) ** 2).sum()
    if sxx <= 0: return None
    b = ((x - xm) * (y - ym)).sum() / sxx; a = ym - b * xm
    s = math.sqrt(((y - a - b * x) ** 2).sum() / max(1, n - 2))
    xe = (END - t[0]).astype(float) / 365.25
    further = b * (xe - x[-1])  # line value at 2029 minus line value at the last date
    return b, s / math.sqrt(sxx), further

def around(P, at):
    k = []
    for i in range(8):
        a = i / 8 * 2 * math.pi
        c = (at[0] + math.cos(a) * RING / (111320 * math.cos(math.radians(at[1]))), at[1] + math.sin(a) * RING / 110540)
        p = pin_series(P, c); f = p and line(p[0], p[1])
        if f: k.append(f[0])
    if len(k) < 4: return None
    k = np.array(k); med = np.median(k)
    return med, 1.4826 * np.median(np.abs(k - med)), k

def verdict(P, at):
    p = pin_series(P, at)
    if not p or len(p[1]) < 2: return None
    f = line(p[0], p[1])
    if not f: return None
    b, sb, further = f
    ar = around(P, at)
    if ar:
        diff = b - ar[0]
        if abs(diff) >= DIFF_MIN and abs(diff) > 2 * ar[1]: return 'differs', b, sb, ar
    if further <= SINK and abs(b) > 2 * sb: return 'sinks', b, sb, ar
    return 'ok', b, sb, ar

def main():
    random.seed(5)
    Z = zones()
    files = {'S1 029A': f'{SITE}/s1/all/points_029A.json', 'S1 007D': f'{SITE}/s1/all/points_007D.json',
             'NISAR 129A': f'{SITE}/nisar/points_129A.json'}
    res = {}
    for name, path in files.items():
        P = load(path); dates, lon, lat = P[0], P[1], P[2]
        c0 = (float(np.median(lon)), float(np.median(lat)))
        # stable spots: inside 5 km of the town centre, more than zone radius + 500 m from every zone
        cand = np.flatnonzero(metres(lon, lat, c0) < 5000)
        far = [i for i in cand if all(metres(lon[i], lat[i], (z[1], z[2])) > z[3] + 500 for z in Z)]
        pick = random.sample(far, min(300, len(far)))
        out = {'differs': 0, 'sinks': 0, 'ok': 0, 'none': 0}; green_on_noise = 0; ratios = []
        for i in pick:
            v = verdict(P, (lon[i], lat[i]))
            if not v: out['none'] += 1; continue
            out[v[0]] += 1
            if v[0] == 'ok' and abs(v[1]) < 2 * v[2]: green_on_noise += 1
            if v[3] is not None:  # honest scatter: neighbours' slopes vs the stated sigma
                ratios.append(1.4826 * np.median(np.abs(v[3][2] - v[3][0])) / max(v[2], 1e-9))
        tested = len(pick) - out['none']
        zone_res = {}
        for z in Z:
            v = verdict(P, (z[1], z[2]))
            zone_res[z[0]] = None if not v else {'rule': v[0], 'slope': round(v[1], 1), 'sigma': round(v[2], 1)}
        res[name] = {'dates': len(dates), 'stable_spots_tested': tested,
                     'not_recommended_on_stable_ground': round((out['differs'] + out['sinks']) / max(tested, 1), 3),
                     'by_uneven_settling': out['differs'], 'by_own_trend': out['sinks'], 'no_warning': out['ok'],
                     'green_while_trend_within_2sigma': round(green_on_noise / max(tested, 1), 3),
                     'neighbour_spread_over_stated_sigma_median': round(float(np.median(ratios)), 1) if ratios else None,
                     'zone_centres_without_the_zone_rule': zone_res}
        print(name, json.dumps(res[name], indent=1), flush=True)
    json.dump(res, open('notebooks/05/pin_redteam.json', 'w'), indent=1)

if __name__ == '__main__':
    main()
