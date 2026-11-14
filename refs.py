# Owner: 04 · Geodesist (Matei)
"""04 · Geodesist: the open references: a velocity model and station rates, all Eurasia-fixed (mm/yr).

Status: STUB (interfaces only).

    python refs.py ocnele_mari     # download EuVeM2022 (Romania grid) and NGL MIDAS (Eurasia-fixed); add published rates
    python refs.py demo            # synthetic site: offline stand-ins with the known truth (and one station that lies)

Writes data/work/<site>/refs/ (never committed). DRAFT hand-off to calibrate.py and validate.py:
    model_euvem.csv    lon, lat, ve, vn, vu, se, sn, su          (0.1° grid)
    stations.csv       station, source, lat, lon, ve, vn, vu, se, sn, su, t_start, t_end
    egms_up.csv        lon, lat, v   ← written by 05 (EGMS L3 Ortho Up tile); refs.py only checks that it is there

The frame, in one paragraph: everything Eurasia-fixed. EuVeM2022 (horizontals ETRF2000, up IGS14), NGL MIDAS
`midas.EU.txt` (IGS14-based) and Muntean et al. 2026 (Eurasia-fixed). NISAR measures relative to its orbits; uniform
plate motion over a 50 km window goes into the tie's offset. Mixing frames between model and stations would not cancel
(25 mm/yr of plate motion can show up as ~10 mm/yr in a line of sight). No ROMPOS data, ever.
"""
from __future__ import annotations

import argparse

import common as C

# DRAFT sources (verify they still answer; see CITATIONS.md)
EUVEM_ROMANIA = "https://www.lantmateriet.se/geodesi_data/EuVeM2022/country_results/EuVeM2022_Romania.txt"
MIDAS_EU = "https://geodesy.unr.edu/velocities/midas.EU.txt"
FIELDS = ["station", "source", "lat", "lon", "ve", "vn", "vu", "se", "sn", "su", "t_start", "t_end"]


def get_model(site: str) -> list[list[float]]:
    """EuVeM2022 Romania grid rows [lon, lat, ve, vn, vu, se, sn, su] (mm/yr)."""
    raise C.todo("04", "download and parse the EuVeM2022 Romania grid")


def get_midas(site: str, wanted: set[str]) -> list[dict]:
    """NGL MIDAS Eurasia-fixed rates for the wanted stations (m/yr in the file → mm/yr), with t_start / t_end."""
    raise C.todo("04", "download midas.EU.txt and keep the window's stations")


def published_rows(site: str) -> list[dict]:
    """Rows for C.PUBLISHED (Muntean et al. 2026). Fill the NaN verticals in common.py from Table S3 first."""
    raise C.todo("04", "turn C.PUBLISHED into station rows")


def synthetic(site: str) -> None:
    """Offline stand-ins: a flat model at the synthetic regional velocity, honest stations, and one that lies (+6 mm/yr up)."""
    raise C.todo("04", "write synthetic model_euvem.csv and stations.csv with a known truth")


def load_model(site: str):
    """→ f(lon, lat) = (ve, vn, vu) interpolated from model_euvem.csv. Used by calibrate.py."""
    raise C.todo("04", "interpolator over the model grid")


def load_stations(site: str) -> list[dict]:
    """→ rows of stations.csv with floats (NaN where empty). Used by calibrate.py and validate.py."""
    raise C.todo("04", "read stations.csv")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    a = ap.parse_args()
    if C.SITES[a.site].get("synthetic"):
        return synthetic(a.site)
    out = C.site_dir(a.site, "refs")
    get_model(a.site)
    get_midas(a.site, set(C.SITES[a.site]["stations"]))
    published_rows(a.site)
    if not (out / "egms_up.csv").exists():
        print("  EGMS Up: not on disk yet (05 writes refs/egms_up.csv); the cross-check will be skipped")
    raise C.todo("04", f"write {out}/model_euvem.csv and stations.csv")


if __name__ == "__main__":
    C.run_cli(main)
