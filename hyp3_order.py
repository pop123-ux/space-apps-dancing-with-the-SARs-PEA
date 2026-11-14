# Owner: 05 · Validator (Paul)
"""05 · Validator: order Sentinel-1 interferograms on ASF HyP3 for the same months as NISAR (the second radar).

Status: STUB (interfaces only). **Order at hour 0–1: HyP3 queues for hours.**

    python hyp3_order.py ocnele_mari --plan      # list the Sentinel-1 pairs that would be ordered (no login)
    python hyp3_order.py ocnele_mari --submit    # submit INSAR_GAMMA jobs (Earthdata login)
    python hyp3_order.py ocnele_mari --status    # job status; download finished products into data/work/<site>/s1/

DRAFT windows (match NISAR, see docs/data.md): 2025-11-01 → 2026-01-31 and 2026-06-15 → 2026-10-31; both Sentinel-1
geometries over the town. Short pairs (6/12 days) plus some longer ones, so the C-band short-pair bias can be checked
(in our 2024–2026 stack 8-day pairs read 20–40 % above 16-day pairs). Mind the HyP3 monthly credit limit per account.

Writes data/work/<site>/s1/ (never committed): jobs.json (what was ordered, by whom, when), then the products.
validate.py check 8 reads the bowl rate from them. Prior work: the salt-events study's hyp3_plan.py has the pattern
(declare it in CITATIONS.md, Prior work, if reused).
"""
from __future__ import annotations

import argparse

import common as C

WINDOWS = [("2025-11-01", "2026-01-31"), ("2026-06-15", "2026-10-31")]   # DRAFT (05)


def plan(site: str) -> list[dict]:
    """Search Sentinel-1 SLCs over the site in WINDOWS → list of (reference, secondary) pairs to order."""
    raise C.todo("05", "search Sentinel-1 (asf_search) and form the pair list")


def submit(site: str, pairs: list[dict]) -> None:
    """Submit INSAR_GAMMA jobs with hyp3_sdk; record them in data/work/<site>/s1/jobs.json."""
    raise C.todo("05", "submit HyP3 jobs and record them")


def status(site: str) -> None:
    """Report job status; download and unzip finished products."""
    raise C.todo("05", "watch and download HyP3 jobs")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("site", choices=["ocnele_mari"])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true")
    g.add_argument("--submit", action="store_true")
    g.add_argument("--status", action="store_true")
    a = ap.parse_args()
    if a.status:
        return status(a.site)
    pairs = plan(a.site)
    if a.submit:
        submit(a.site, pairs)


if __name__ == "__main__":
    C.run_cli(main)
