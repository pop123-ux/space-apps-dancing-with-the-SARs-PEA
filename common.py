# Owner: shared · announce changes; 01 reviews
"""Shared settings and small helpers. Every script imports this as `import common as C`.

A value changed here changes everyone's results, so announce it to the team and get the Lead's (01) OK in
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
        # Salt zones kept out of the tie and used for zone medians. Positions from the advisor kit. Names (14 Nov 2026)
        # from the nearest mapped place (OpenStreetMap, Overpass) matched to INFO.md and ocnele-mari-geography.md:
        # z1 centre lies 10 m from the salt lake "Lacul Țeica", the 2001 collapse over Câmpul II de sonde (Dealul Țeica);
        # z2 is the ground just east of that lake (190 m); z3 is the Goruniș quarter of Ocnița (420 m), next to Lunca;
        # z4 is the village of Slătioarele, Coșota (230 m). `place` says where each name comes from.
        zones=[
            dict(id="z1", name="Lacul Țeica", lat=45.0892, lon=24.2872, r_m=300,
                 place="2001 collapse lake over Câmpul II de sonde, Dealul Țeica"),
            dict(id="z2", name="Țeica east", lat=45.0882, lon=24.2892, r_m=250,
                 place="Ground just east of Lacul Țeica, on the same brine field"),
            dict(id="z3", name="Ocnița · Goruniș", lat=45.0930, lon=24.2565, r_m=300,
                 place="Goruniș quarter of Ocnița, next to Lunca: the old Ocnița mine and its collapse lakes"),
            dict(id="z4", name="Slătioarele", lat=45.0826, lon=24.2628, r_m=250,
                 place="Village of Slătioarele, Coșota"),
        ],
        stations=["VLC1", "VLC2", "HORE"],   # DRAFT (04/05): open stations inside the window
        story="TODO(01): one sentence, written by the Lead",
        # D-002 (locked): the map opens on the town; zooming out shows Romania, blurred, as context only.
        view=dict(center=[45.086281, 24.2704806], zoom=13),
    ),
}
SITES["demo"] = dict(SITES["ocnele_mari"], name="Ocnele Mari · synthetic demo", synthetic=True,
                     story="Invented ground motion with a known answer. Simulated, not data.")

# ---------------------------------------------------------------------------------------------------------- sensors
# D-004 (locked): we fit both NISAR and Sentinel-1, and the page switches between them (docs/ui.md).
# Tracks and dates checked on NASA CMR and in sentinel1/analysis/summary.json, 14 Nov 2026. The page's labels come from
# here through export.py, so a sensor is described once. Keys are used in file names: products/<site>/<sensor>/…
SENSORS = {
    "nisar": dict(
        label="NISAR", agency="NASA–ISRO", band="L-band", wavelength_cm=24.4, look="left",
        product="NISAR L2 GUNW, frequency A, HH (beta and provisional)", status="beta/provisional",
        tracks={"129A": "Ascending", "094D": "Descending"},
        reference="tied to the EuVeM2022 velocity model (04; DRAFT until the tie exists)",
        credit="NISAR L2 GUNW (NASA–ISRO, ASF DAAC); beta and provisional products, not intended for scientific research",
        fitted_by="fetch.py (02) → stack.py (03) → calibrate.py (04)"),
    "s1": dict(
        label="Sentinel-1", agency="ESA / Copernicus", band="C-band", wavelength_cm=5.55, look="right",
        product="Sentinel-1C/D VV burst InSAR, ASF HyP3 INSAR_ISCE_BURST, 10x2 looks", status="operational",
        tracks={"029A": "Ascending", "007D": "Descending"},
        reference="relative to surrounding terrain, a 3 to 6.5 km band (sentinel1/analysis/README.md)",
        credit="Contains modified Copernicus Sentinel data 2026, processed by ASF HyP3",
        fitted_by="sentinel1/scripts/fit.py (03)"),
}
COMMON_WINDOW = ("2026-07-07", "2026-10-04")   # dates both sensors cover: Sentinel-1 fit window inside NISAR's Jun to Oct
VIEWS = ("change", "rate", "zones", "agreement", "coverage")   # the page's view switch (docs/ui.md)

# Published station rates: Muntean et al. 2026, Solid Earth 17, 747–762, supplement Tables S1/S3, Eurasia-fixed.
# station: (lat, lon, ve, vn, vu, se, sn, su) in mm/yr; NaN = not published. Owner 04 fills the vertical from Table S3.
# Cite the paper; do not copy the table into the repository (open question Q4 on quoting it in the app).
# VLC2 east/north and uncertainties use Table S1's Vlon/Vlat and Siglon/Siglat columns.
# VLC2 up comes from Table S3. HORE has no Table S3 entry. Its separate historical up rate is from NGL MIDAS.
_nan = float("nan")
PUBLISHED = {
    "VLC2": (45.1074, 24.3664, -0.84, 0.77, 0.86, 0.21, 0.19, 0.61),
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
def zone_label(z: dict) -> str:
    """A zone's display name: its place name, or 'Zone N' while it has none."""
    name = str(z.get("name") or "")
    return name if name and not name.startswith("TODO") else f"Zone {z['id'].lstrip('z')}"


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
