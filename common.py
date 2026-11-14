"""Shared settings and small helpers. Every script imports this as `import common as C`.

Owner: shared. A value changed here changes everyone's results, so announce it to the team and get the Lead's (01) OK in
the PR. Nothing here talks to the network, and nothing heavy is imported at the top, so `python <script>.py --help`
works on a bare Python before the environment is installed.

Values marked DRAFT are starting points, most of them from the advisor's rehearsal kit (prior work, see
CITATIONS.md). The role named next to each value confirms or changes it.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

for _s in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"            # git-ignored
WORK = DATA / "work"            # data/work/<site>/<track>/ … intermediates between steps
PRODUCTS = ROOT / "products"    # products/<site>/ … the only thing the page reads
DOCS = ROOT / "docs"

ROLES = {"01": "Lead & story", "02": "NISAR data", "03": "InSAR analyst",
         "04": "Geodesist", "05": "Validator", "06": "App developer"}
STUB_EXIT = 3   # exit code of a step that is not implemented yet (run_all.py stops cleanly on it)

# ------------------------------------------------------------------------------------------------------------ sites
# D-001 (locked): Ocnele Mari is the only site of analysis.
# "demo" is not a second site: it is the synthetic known-answer test (Ocnele Mari geometry, invented motion with a known
# truth) that must stay green once the synthetic chain exists.
SITES = {
    "ocnele_mari": dict(
        name="Ocnele Mari",
        county="Vâlcea",
        lat=45.088, lon=24.290,     # DRAFT (02/04) analysis-window centre; town pin is 45.0838382, 24.2859745
        half_km=25,                 # DRAFT (04/05) half-size of the analysis window: big enough for stable ground and stations
        height_m=400,               # DRAFT (02) reference height for the line-of-sight vectors
        # DRAFT (03 with 01): salt zones kept out of the tie and used for zone medians. Positions from the advisor kit;
        # names still to be matched to INFO.md (Țeica/Socon, Câmpul I and II de sonde, Lunca, Ocnița).
        zones=[
            dict(id="z1", name="TODO", lat=45.0892, lon=24.2872, r_m=300),
            dict(id="z2", name="TODO", lat=45.0882, lon=24.2892, r_m=250),
            dict(id="z3", name="TODO", lat=45.0930, lon=24.2565, r_m=300),
            dict(id="z4", name="TODO", lat=45.0826, lon=24.2628, r_m=250),
        ],
        stations=["VLC1", "VLC2", "HORE"],   # DRAFT (04/05): open stations inside the window
        story="TODO(01): one sentence, written by the Lead",
        # D-002 (locked): the map opens on the town; zooming out shows Romania, blurred, as context only.
        view=dict(center=[45.086281, 24.2704806], zoom=13),
    ),
}
SITES["demo"] = dict(SITES["ocnele_mari"], name="Ocnele Mari · synthetic demo", synthetic=True,
                     story="Invented ground motion with a known answer. Simulated, not data.")

# Published station rates: Muntean et al. 2026, Solid Earth 17, 747–762, supplement Tables S1/S3, Eurasia-fixed.
# station: (lat, lon, ve, vn, vu, se, sn, su) in mm/yr; NaN = not published. Owner 04 fills the vertical from Table S3.
# Cite the paper; do not copy the table into the repository (open question Q4 on quoting it in the app).
# 04, 14 Nov 2026: VLC2 vu 0.86 ± 0.61 mm/yr from Table S3 (Tstart 2 Aug 2019, span 5.82 yr; the PDF row runs its
# fields together, the split is confirmed by su = 0.61 already read). HORE is not in Table S3: its vertical stays NaN
# here and comes from NGL MIDAS instead.
_nan = float("nan")
PUBLISHED = {
    "VLC2": (45.1074, 24.3664, 0.15, 0.14, 0.86, 0.21, 0.19, 0.61),
    "HORE": (45.1456, 23.9891, -0.50, 0.41, _nan, 0.09, 0.11, _nan),
}

# --------------------------------------------------------------------------------------------- thresholds (DRAFT)
NISAR_START = "2025-10-01"      # (02) search start
LIGHT = 299_792_458.0           # m/s
MIN_COH = 0.35                  # (03) a pixel's pair is used above this coherence
MIN_VALID_PAIRS = 0.6           # (03) share of pairs a pixel needs to get a time series
ANNUAL_TERM_MIN_YEARS = 1.5     # (03) no annual term below this span
EXCLUDE_KM = 3.0                # (04) salt zones + this margin stay out of the tie
TIE_MIN_COH = 0.4               # (04) tie pixels need this mean coherence
STATION_HOLDOUT_M = 1000        # (04/05) pixels this close to a station stay out of the tie
TOL_FLOOR = 2.0                 # (05) mm/yr: station and NISAR agree below this whatever the formal errors


# --------------------------------------------------------------------------------------------------------- helpers
def todo(role: str, what: str) -> NotImplementedError:
    """Build the error a stub raises: `raise C.todo("02", "stream the window")`."""
    return NotImplementedError(f"TODO({role} · {ROLES[role]}): {what}")


def run_cli(main):
    """Run a script's main(); a stub step exits with STUB_EXIT and one readable line instead of a traceback."""
    try:
        return main()
    except NotImplementedError as e:
        print(f"⏳ not implemented yet: {e}", file=sys.stderr)
        sys.exit(STUB_EXIT)


def site_dir(site: str, *parts: str) -> pathlib.Path:
    """data/work/<site>/<parts…>, created on first use."""
    p = WORK.joinpath(site, *parts)
    p.mkdir(parents=True, exist_ok=True)
    return p


def tracks(site: str) -> list[str]:
    """Tracks fetched for a site: folders under data/work/<site>/ with a meta.json (e.g. ['094D', '129A'])."""
    d = WORK / site
    return sorted(p.name for p in d.iterdir() if (p / "meta.json").exists()) if d.exists() else []


def load_json(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def save_json(p, obj) -> None:
    p = pathlib.Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=float), encoding="utf-8")


def utm_epsg(lon: float, lat: float) -> int:
    return (32600 if lat >= 0 else 32700) + int((lon + 180) // 6) + 1


def to_xy(epsg: int, lon, lat):
    from pyproj import Transformer
    return Transformer.from_crs(4326, epsg, always_xy=True).transform(lon, lat)


def to_lonlat(epsg: int, x, y):
    from pyproj import Transformer
    return Transformer.from_crs(epsg, 4326, always_xy=True).transform(x, y)


def years(dates):
    """Decimal years since 2026-01-01 (the convention for every fit)."""
    import numpy as np
    d = np.array(dates, dtype="datetime64[D]")
    return (d - np.datetime64("2026-01-01")).astype(float) / 365.25


def enu_to_los(e, n, u, ve, vn, vu):
    """Velocity (ENU, mm/yr) onto a line of sight given as a target→sensor unit vector: positive = towards the satellite."""
    return e * ve + n * vn + u * vu


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))
