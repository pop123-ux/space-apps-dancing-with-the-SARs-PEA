"""04 · Geodesist: the open references: a velocity model and station rates, all Eurasia-fixed (mm/yr).

Owner: 04 · Geodesist (Matei). Status: WORKING (synthetic path tested offline; real path to be run on a laptop with
internet, the build machine could not reach the two servers on 14 Nov 2026).

    python refs.py ocnele_mari            # download EuVeM2022 (Romania grid) and NGL MIDAS (Eurasia-fixed); add published rates
    python refs.py ocnele_mari --cached   # reuse data/raw/refs/ instead of downloading again
    python refs.py demo                   # synthetic site: offline stand-ins with the known truth (and one station that lies)

Writes data/work/<site>/refs/ (never committed). Hand-off to calibrate.py and validate.py:
    model_euvem.csv    lon, lat, ve, vn, vu, se, sn, su          (0.1° grid)
    stations.csv       station, source, lat, lon, ve, vn, vu, se, sn, su, t_start, t_end
    egms_up.csv        lon, lat, v   ← written by 05 (EGMS L3 Ortho Up tile); refs.py only checks that it is there
    truth.json         (synthetic only) the regional velocity and the name of the station that lies
Raw downloads are cached in data/raw/refs/ (never committed).

The frame, in one paragraph: everything Eurasia-fixed. EuVeM2022 (horizontals ETRF2000, up IGS14), NGL MIDAS
`midas.EU.txt` (IGS14-based) and Muntean et al. 2026 (Eurasia-fixed). NISAR measures relative to its orbits; uniform
plate motion over a 50 km window goes into the tie's offset. Mixing frames between model and stations would not cancel
(25 mm/yr of plate motion can show up as ~10 mm/yr in a line of sight). No ROMPOS data, ever.

Station names are not unique across Europe: NGL MIDAS has a "VLC2" in Italy (43.28° N, 12.28° E), 977 km from the town.
So a MIDAS row is kept only when it lies within the analysis window's half-diagonal of the window centre, and every
open MIDAS station inside that radius is kept, named in the site list or not.
"""
from __future__ import annotations

import argparse
import csv
import json
import math

import common as C

# Sources (checked against the advisor kit; see CITATIONS.md)
EUVEM_ROMANIA = "https://www.lantmateriet.se/geodesi_data/EuVeM2022/country_results/EuVeM2022_Romania.txt"
MIDAS_EU = "https://geodesy.unr.edu/velocities/midas.EU.txt"
UA = {"User-Agent": "dancing-on-salt/0.2 (NASA Space Apps 2026)"}
FIELDS = ["station", "source", "lat", "lon", "ve", "vn", "vu", "se", "sn", "su", "t_start", "t_end"]
MODEL_FIELDS = ["lon", "lat", "ve", "vn", "vu", "se", "sn", "su"]

# Time span of the published rates (Muntean et al. 2026, Table S3: Tstart, Tspan in years). HORE is not in Table S3.
PUBLISHED_SPAN = {"VLC2": ("2019-08-02", "2025.41")}

# Synthetic site: a regional velocity (Eurasia-fixed, mm/yr) and one station that lies (a mast moving +6 mm/yr up).
SYNTH_REGIONAL = dict(ve=0.3, vn=-0.4, vu=-0.2)
SYNTH_LIAR = ("VLC1", 6.0)


# ---------------------------------------------------------------------------------------------------------- helpers
def raw_dir():
    p = C.DATA / "raw" / "refs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def download(url: str, cached: bool) -> str:
    """Text of url, cached in data/raw/refs/<file name>. With cached=True, reuse the file if it is there."""
    p = raw_dir() / url.rsplit("/", 1)[-1]
    if cached and p.exists():
        print(f"  cached: {p.name}")
        return p.read_text(encoding="utf-8", errors="replace")
    import requests
    r = requests.get(url, headers=UA, timeout=180)
    r.raise_for_status()
    p.write_text(r.text, encoding="utf-8")
    print(f"  downloaded: {p.name} ({len(r.content) / 1e6:.1f} MB)")
    return r.text


def window_radius_km(site: str) -> float:
    """Half-diagonal of the square analysis window: a station farther than this cannot lie inside it."""
    return C.SITES[site]["half_km"] * math.sqrt(2)


def dist_km(site: str, lat: float, lon: float) -> float:
    s = C.SITES[site]
    return C.haversine_km(s["lat"], s["lon"], lat, lon)


def _float(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return math.nan


# ------------------------------------------------------------------------------------------------------- the model
def parse_euvem(text: str) -> list[list[float]]:
    """EuVeM2022 country file: lines of lon lat ve vn vu se sn su (mm/yr). Comment or header lines are skipped."""
    rows, skipped = [], 0
    for line in text.splitlines():
        p = line.replace(",", " ").split()
        if not p or line.lstrip().startswith(("#", "%", "!")):
            continue
        try:
            rows.append([float(v) for v in p[:8]])
        except ValueError:
            skipped += 1
            continue
        if len(rows[-1]) < 8:
            raise ValueError(f"EuVeM2022 line has {len(p)} columns, expected at least 8: {line!r}")
    if not rows:
        raise ValueError("EuVeM2022: no numeric lines found; has the file format changed?")
    lons = [r[0] for r in rows]
    lats = [r[1] for r in rows]
    if not (19 <= min(lons) and max(lons) <= 31 and 43 <= min(lats) and max(lats) <= 49):
        raise ValueError(f"EuVeM2022: columns 1-2 span lon {min(lons)}..{max(lons)}, lat {min(lats)}..{max(lats)}, "
                         "which is not Romania; check the column order")
    if skipped:
        print(f"  EuVeM2022: skipped {skipped} non-numeric lines (headers)")
    return rows


def get_model(site: str, cached: bool = False) -> list[list[float]]:
    """EuVeM2022 Romania grid rows [lon, lat, ve, vn, vu, se, sn, su] (mm/yr)."""
    rows = parse_euvem(download(EUVEM_ROMANIA, cached))
    s = C.SITES[site]
    lons = [r[0] for r in rows]
    lats = [r[1] for r in rows]
    if not (min(lons) < s["lon"] < max(lons) and min(lats) < s["lat"] < max(lats)):
        raise ValueError("EuVeM2022 grid does not cover the site centre")
    return rows


# ---------------------------------------------------------------------------------------------------- the stations
def parse_midas(text: str) -> list[dict]:
    """NGL MIDAS midas.EU.txt (Eurasia-fixed, IGS14-based). Columns (1-based): 1 station, 3-4 first and last epoch
    (decimal years), 9-11 ve vn vu and 12-14 se sn su in m/yr, 25 lat, 26 lon (may be shifted by -360), 27 height."""
    out = []
    for line in text.splitlines():
        p = line.split()
        if len(p) < 26:
            continue
        try:
            ve, vn, vu, se, sn, su = (float(v) * 1000 for v in p[8:14])
            lat, lon = float(p[24]), (float(p[25]) + 180) % 360 - 180
        except ValueError:
            continue
        out.append(dict(station=p[0], source="NGL MIDAS (EU-fixed)", lat=lat, lon=lon,
                        ve=ve, vn=vn, vu=vu, se=se, sn=sn, su=su, t_start=p[2], t_end=p[3]))
    if not out:
        raise ValueError("NGL MIDAS: no station lines parsed; has the file format changed?")
    return out


def select_midas(site: str, rows: list[dict], wanted: set[str]) -> list[dict]:
    """Keep MIDAS rows inside the window radius. A wanted name found only far away is reported and dropped."""
    r_max = window_radius_km(site)
    kept = []
    for r in rows:
        d = dist_km(site, r["lat"], r["lon"])
        if d <= r_max:
            kept.append(r)
        elif r["station"] in wanted:
            print(f"  dropped MIDAS {r['station']} at {r['lat']:.3f}, {r['lon']:.3f}: {d:.0f} km away, "
                  f"a different station with the same name")
    extra = sorted({r["station"] for r in kept} - wanted)
    if extra:
        print(f"  MIDAS stations inside {r_max:.0f} km not in the site list (kept): {', '.join(extra)}")
    return kept


def get_midas(site: str, wanted: set[str], cached: bool = False) -> list[dict]:
    """NGL MIDAS Eurasia-fixed rates near the site (m/yr in the file → mm/yr), with t_start / t_end."""
    return select_midas(site, parse_midas(download(MIDAS_EU, cached)), wanted)


def published_rows(site: str) -> list[dict]:
    """Rows for C.PUBLISHED (Muntean et al. 2026), inside the window radius. NaN where the paper gives no value."""
    rows = []
    for st, (la, lo, ve, vn, vu, se, sn, su) in C.PUBLISHED.items():
        if dist_km(site, la, lo) > window_radius_km(site):
            continue
        t0, t1 = PUBLISHED_SPAN.get(st, ("", ""))
        rows.append(dict(station=st, source="Muntean et al. 2026", lat=la, lon=lo, ve=ve, vn=vn, vu=vu,
                         se=se, sn=sn, su=su, t_start=t0, t_end=t1))
    return rows


# ------------------------------------------------------------------------------------------------------- synthetic
def synthetic(site: str) -> None:
    """Offline stand-ins: a flat model at the synthetic regional velocity, honest stations, and one that lies (+6 mm/yr up)."""
    import numpy as np
    out = C.site_dir(site, "refs")
    s, r = C.SITES[site], SYNTH_REGIONAL
    lon0, lat0 = round(s["lon"], 1), round(s["lat"], 1)
    grid = [[round(lo, 1), round(la, 1), r["ve"], r["vn"], r["vu"], 0.5, 0.5, 0.3]
            for lo in np.arange(lon0 - 1.0, lon0 + 1.05, 0.1) for la in np.arange(lat0 - 1.0, lat0 + 1.05, 0.1)]
    rng = np.random.default_rng(2026)
    coords = {"VLC1": (45.1074, 24.3664), "VLC2": (45.1074, 24.3664), "HORE": (45.1456, 23.9891)}
    rows = []
    for st in s["stations"]:
        la, lo = coords[st]
        lie = SYNTH_LIAR[1] if st == SYNTH_LIAR[0] else 0.0
        rows.append(dict(station=st, source="synthetic", lat=la, lon=lo,
                         ve=r["ve"] + rng.normal(0, 0.2), vn=r["vn"] + rng.normal(0, 0.2),
                         vu=r["vu"] + lie + rng.normal(0, 0.3), se=0.2, sn=0.2, su=0.4,
                         t_start="2013.0", t_end="2025.0"))
    write(out, grid, rows)
    C.save_json(out / "truth.json", dict(synthetic=True, regional=r, liar=SYNTH_LIAR[0], liar_vu_mm_yr=SYNTH_LIAR[1],
                                         note="Simulated, not data"))
    print(f"{site}: synthetic model {len(grid)} nodes at ve {r['ve']}, vn {r['vn']}, vu {r['vu']} mm/yr · "
          f"stations {', '.join(x['station'] for x in rows)} (one lies) · Simulated, not data")


# ----------------------------------------------------------------------------------------------------- write, load
def write(out, grid, rows) -> None:
    with open(out / "model_euvem.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(MODEL_FIELDS)
        w.writerows(grid)
    with open(out / "stations.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)


def model_file(site: str, model: str = "euvem"):
    return C.site_dir(site, "refs") / f"model_{model}.csv"


def load_model(site: str, model: str = "euvem"):
    """→ f(lon, lat) = array (..., 3) of (ve, vn, vu), linear inside the grid, NaN outside. Used by calibrate.py.
    model='egms' reads model_egms.csv, written by hand in the same columns once its CSV is found (O-06)."""
    import numpy as np
    from scipy.interpolate import LinearNDInterpolator
    p = model_file(site, model)
    if not p.exists():
        raise FileNotFoundError(f"{p} is missing: run `python refs.py {site}` (or add model_{model}.csv)")
    a = np.genfromtxt(p, delimiter=",", names=True)
    f = LinearNDInterpolator(np.c_[a["lon"], a["lat"]], np.c_[a["ve"], a["vn"], a["vu"]])

    def at(lon, lat):
        lon, lat = np.asarray(lon, float), np.asarray(lat, float)
        return f(np.c_[lon.ravel(), lat.ravel()]).reshape(lon.shape + (3,))
    return at


def load_stations(site: str) -> list[dict]:
    """→ rows of stations.csv with floats (NaN where empty). Used by calibrate.py and validate.py."""
    p = C.site_dir(site, "refs") / "stations.csv"
    if not p.exists():
        raise FileNotFoundError(f"{p} is missing: run `python refs.py {site}`")
    with open(p, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("lat", "lon", "ve", "vn", "vu", "se", "sn", "su"):
            r[k] = _float(r[k])
    return rows


# ------------------------------------------------------------------------------------------------------------ main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    ap.add_argument("--cached", action="store_true", help="reuse downloads in data/raw/refs/ when present")
    a = ap.parse_args()
    if C.SITES[a.site].get("synthetic"):
        return synthetic(a.site)
    out = C.site_dir(a.site, "refs")
    wanted = set(C.SITES[a.site]["stations"])
    grid = get_model(a.site, a.cached)
    rows = get_midas(a.site, wanted, a.cached) + published_rows(a.site)
    write(out, grid, rows)
    near = sum(1 for g in grid if dist_km(a.site, g[1], g[0]) <= window_radius_km(a.site))
    print(f"{a.site}: model {len(grid)} grid nodes ({near} inside the window) · stations: "
          + ", ".join(f"{r['station']} ({r['source'].split(' ')[0]}, {dist_km(a.site, r['lat'], r['lon']):.1f} km, "
                      f"vu {r['vu']:+.2f})" for r in rows))
    missing = wanted - {r["station"] for r in rows}
    if missing:
        print("  no open rate for:", ", ".join(sorted(missing)))
    no_up = sorted({r["station"] for r in rows if math.isnan(r["vu"])} - {r["station"] for r in rows
                                                                         if not math.isnan(r["vu"])})
    if no_up:
        print("  no vertical rate from any source for:", ", ".join(no_up))
    if not (out / "egms_up.csv").exists():
        print("  EGMS Up: not on disk yet (05 writes refs/egms_up.csv); the cross-check will be skipped")


if __name__ == "__main__":
    C.run_cli(main)
