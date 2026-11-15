# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Acquisition-time tropospheric delay versus height for each Sentinel-1 date, from a weather model.

    python tropo.py SUMMARY_JSON [SUMMARY_JSON ...] -o tropo.json

For every track and date in the summaries, fetch the ECMWF IFS 0.25° pressure-level profile (temperature, relative
humidity, geopotential height; 18 levels, hourly) over Ocnele Mari from the Open-Meteo historical-forecast API, at the
track's acquisition time (029A 16:16 UTC, 007D 04:29 UTC; linear in time between the two nearest hours). Integrate the
refractivity N = k1 P/T + k2' e/T + k3 e/T^2 from each height up to the top level to get the zenith total delay ZTD(h)
in mm. Only differences between dates and heights matter to the fit (the delay above the top level is the same for every
pixel), so ZTD is reported relative to its value at 2,000 m.

fit.py --tropo tropo.json then removes, from each interferogram, [ZTD_secondary(h) - ZTD_reference(h)] / cos(incidence) (= / sin(lv_theta))
at every pixel's DEM height: the stratified (elevation-dependent) delay. Turbulent, horizontally varying delay is not
modelled: one profile serves the whole 16 km window.
"""
from pathlib import Path
import argparse
import json
from urllib.request import urlopen

import numpy as np

LAT, LON = 45.088, 24.290
LEVELS = [1000, 975, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100, 70, 50]
HOURS_UTC = {'029A': 16 + 16.6 / 60, '007D': 4 + 29.2 / 60}
K1, K2P, K3 = 77.6, 23.3, 3.75e5            # K/hPa, K/hPa, K^2/hPa (Smith and Weintraub; Thayer)
HEIGHTS = np.arange(0.0, 2001.0, 10.0)      # m; the window spans about 175 to 1,000 m
API = 'https://historical-forecast-api.open-meteo.com/v1/forecast'


def fetch(start, end, tries=5):
    """All hourly profiles from start to end (ISO days) in one request; retried on network errors."""
    import time
    vars_ = [f'{v}_{p}hPa' for p in LEVELS for v in ('temperature', 'relative_humidity', 'geopotential_height')]
    url = (f'{API}?latitude={LAT}&longitude={LON}&start_date={start}&end_date={end}&models=ecmwf_ifs025'
           f'&hourly={",".join(vars_)}')
    for k in range(tries):
        try:
            with urlopen(url, timeout=120) as r:
                return json.load(r)['hourly']
        except (OSError, ValueError):     # ValueError: an empty or cut reply that is not JSON
            if k == tries - 1:
                raise
            time.sleep(2 ** k)


def day_slice(hourly, day):
    i = hourly['time'].index(f'{day}T00:00')
    return {k: v[i:i + 24] for k, v in hourly.items()}


def ztd_profile(hourly, hour):
    """Zenith total delay (mm) at HEIGHTS, relative to 2,000 m, interpolated linearly to the acquisition hour."""
    h0 = int(np.floor(hour)); w = hour - h0
    out = []
    for h in (h0, min(h0 + 1, 23)):
        rows = [(p, hourly[f'temperature_{p}hPa'][h], hourly[f'relative_humidity_{p}hPa'][h],
                 hourly[f'geopotential_height_{p}hPa'][h]) for p in LEVELS]
        rows = [r for r in rows if None not in r]           # some levels are missing at some hours
        if len(rows) < 8:
            raise ValueError(f'only {len(rows)} complete pressure levels at hour {h}')
        P, T, RH, Z = (np.array(c, float) for c in zip(*rows))
        T = T + 273.15
        Tc = T - 273.15
        e = RH / 100 * 6.112 * np.exp(17.67 * Tc / (Tc + 243.5))
        N = K1 * P / T + K2P * e / T + K3 * e / T ** 2
        order = np.argsort(Z)
        Z, N = Z[order], N[order]
        fine = np.linspace(min(Z[0], 0.0), Z[-1], 4000)
        Nf = np.interp(fine, Z, N)                          # below the lowest level: hold the lowest value
        cum = np.concatenate([[0], np.cumsum((Nf[1:] + Nf[:-1]) / 2 * np.diff(fine))])
        above = (cum[-1] - np.interp(HEIGHTS, fine, cum)) * 1e-6 * 1000    # mm of delay above each height
        out.append(above - np.interp(2000.0, HEIGHTS, above))
    return (1 - w) * out[0] + w * out[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('summaries', nargs='+', type=Path)
    ap.add_argument('-o', '--output', type=Path, required=True)
    a = ap.parse_args()
    wanted = {}
    for s in a.summaries:
        for track, v in json.loads(s.read_text()).items():
            wanted.setdefault(track, set()).update(v['dates'])
    result = dict(source='ECMWF IFS 0.25° via Open-Meteo historical-forecast API (models=ecmwf_ifs025)',
                  location=[LAT, LON], hours_utc=HOURS_UTC, heights_m=HEIGHTS.tolist(),
                  units='mm zenith total delay relative to 2,000 m', tracks={})
    days = sorted(f'{d[:4]}-{d[4:6]}-{d[6:]}' for ds in wanted.values() for d in ds)
    hourly = None   # month by month: one request for ten months came back empty (15 Nov 2026); same hourly values
    from datetime import date, timedelta
    start, last = date.fromisoformat(days[0]), date.fromisoformat(days[-1])
    while start <= last:
        end = min(last, (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1))
        part = fetch(start.isoformat(), end.isoformat())
        hourly = part if hourly is None else {k: hourly[k] + part[k] for k in hourly}
        start = end + timedelta(days=1)
    for track, dates in sorted(wanted.items()):
        result['tracks'][track] = {}
        for d in sorted(dates):
            day = f'{d[:4]}-{d[4:6]}-{d[6:]}'
            result['tracks'][track][d] = np.round(ztd_profile(day_slice(hourly, day), HOURS_UTC[track]), 3).tolist()
            print(track, d, f'ZTD(200 m) - ZTD(800 m) = {np.interp(200, HEIGHTS, result["tracks"][track][d]) - np.interp(800, HEIGHTS, result["tracks"][track][d]):.1f} mm', flush=True)
    a.output.write_text(json.dumps(result) + '\n')


if __name__ == '__main__':
    main()
