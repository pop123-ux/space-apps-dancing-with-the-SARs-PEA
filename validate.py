"""05 · Validator — the checks the team did not tune. Nobody else edits this file.

Owner: 05 · Validator (Paul). Status: STUB (interfaces only).

    python validate.py ocnele_mari

Writes products/<site>/ (contract, see docs/contract.md):
    checks.json        [{id, status: pass|warn|fail|info, title, detail, value}]
    checks.md          the same, readable
    stations.geojson   per station: tracks {nisar, gnss, diff, tol}, agree (true|false|null), reason, nisar_up, gnss_up

The checks (DRAFT thresholds from the advisor kit; 05 owns them):
1 sign      salt zones sink on every track: median LOS rate in the zones < −2 mm/yr, else the phase sign is wrong.
            (Rehearsal: 129A −4.6, 094D +27.5 mm/yr → not confirmed on real data.)
2 stations  held-out stations in each LOS: |NISAR − GNSS| ≤ max(C.TOL_FLOOR, 2σ combined). Old series (2018–2020) are
            flagged "assumes steady motion since". Stations can lie: check the monument (HAR1 mast) before blaming radar.
3 tie       robust scatter of the model tie < 6 mm/yr per pixel (rehearsal: 37 / 51 → WARN).
4 closure   12 + 12 against 24-day pairs over the same dates: ratio 0.8–1.2 (Ocnele Mari GUNW: 0 triplets → info).
5 gaps      dates no pair spans (129A: 18 Jan → 23 Jun 2026): listed, slider must show "no data" there.
6 egms      EGMS Ortho Up 2020–2024, stable ground: median |NISAR − EGMS| < 1.5 mm/yr; the bowl then vs now is reported,
            not judged (a difference is the story, not an error).
7 truth     synthetic site only: up bias < 1 mm/yr, zones within 15 %.
8 s1        Sentinel-1 (HyP3) over the bowl for the same months: same zone rate within the errors (hyp3_order.py).
"""
from __future__ import annotations

import argparse

import common as C

STATUSES = ("pass", "warn", "fail", "info")


def pick(meta: dict, arr, lon: float, lat: float, r_px: int = 2) -> float:
    """Median of arr within r_px pixels of a point, NaN outside the window."""
    raise C.todo("05", "sample a grid at a point")


def check_sign(site, add):      raise C.todo("05", "check 1: salt zones sink on every track")
def check_stations(site, add):  raise C.todo("05", "check 2: held-out stations per LOS → stations.geojson")
def check_tie(site, add):       raise C.todo("05", "check 3: tie scatter from calib.json")
def check_closure(site, add):   raise C.todo("05", "check 4: 12- vs 24-day closure")
def check_gaps(site, add):      raise C.todo("05", "check 5: chain gaps")
def check_egms(site, add):      raise C.todo("05", "check 6: EGMS Ortho stable ground; bowl then vs now")
def check_truth(site, add):     raise C.todo("05", "check 7: synthetic truth recovered (demo only)")
def check_sentinel1(site, add): raise C.todo("05", "check 8: Sentinel-1 bowl rate, same months")


def run(site: str) -> list[dict]:
    checks: list[dict] = []

    def add(id, status, title, detail, value=None):
        assert status in STATUSES, status
        checks.append(dict(id=id, status=status, title=title, detail=detail, value=value))

    for check in (check_sign, check_stations, check_tie, check_closure, check_gaps, check_egms, check_sentinel1):
        check(site, add)
    if C.SITES[site].get("synthetic"):
        check_truth(site, add)
    C.save_json(C.PRODUCTS / site / "checks.json", checks)
    raise C.todo("05", f"write products/{site}/checks.md and print one line per check")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=C.SITES)
    run(ap.parse_args().site)


if __name__ == "__main__":
    C.run_cli(main)
